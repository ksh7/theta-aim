from datetime import datetime
import os
import json
import random
import string

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse, FileResponse
from wsgiref.util import FileWrapper
from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django_htmx.http import trigger_client_event

from web_app.settings import MEDIA_URL, BASE_DIR

from . import models
from . import forms
from . import tasks
from . import utils


def index(request):
    context = {'inference_apps': models.ModelInference.objects.filter(status='Production')}
    return render(request, 'inference_portal/index.html', context)


def explore_apps(request):
    context = {'inference_apps': models.ModelInference.objects.filter(status='Production', release_as_web_app=True)}
    return render(request, 'inference_portal/explore_web_apps.html', context)


def explore_plugins(request):
    context = {'inference_apps': models.ModelInference.objects.filter(status='Production', release_as_plugin=True)}
    return render(request, 'inference_portal/explore_plugins.html', context)


def explore_rest_apis(request):
    context = {'inference_apps': models.ModelInference.objects.filter(status='Production', release_as_api=True)}
    return render(request, 'inference_portal/explore_rest_apis.html', context)


def explore_binaries(request):
    context = {'inference_apps': models.ModelInference.objects.filter(status='Production', release_as_binary=True)}
    return render(request, 'inference_portal/explore_binaries.html', context)


@login_required
def order_details(request, order_id):
    order = models.OrderTransaction.objects.get(id=order_id)
    return render(request, 'inference_portal/order_details.html', {'order': order})


@login_required
def my_purchase_orders(request):
    orders = models.OrderTransaction.objects.filter(buyer=request.user)
    return render(request, 'inference_portal/purchase_orders.html', {'orders': orders})


@login_required
def my_sell_orders(request):
    orders = models.OrderTransaction.objects.filter(seller=request.user)
    return render(request, 'inference_portal/order_details.html', {'orders': orders})


def generate_random_string(length):
  characters = string.ascii_letters + string.digits
  return ''.join(random.choice(characters) for _ in range(length))

def process_order(model_inference_id, service_name, service_type, amount, current_user):
    model_inference = models.ModelInference.objects.get(id=int(model_inference_id))
    order = models.OrderTransaction.objects.create(model_inference=model_inference, service_name=service_name, service_type=service_type, 
                                                   amount=amount, payment_type='TFUEL', seller=model_inference.user, buyer=current_user)
 
    if order.service_name == "rest_api":
        rest_api, created = models.RESTAPI.objects.get_or_create(order=order)
        rest_api.api_endpoint = "https://api-model-id-kjrehghkjgvhdsfkg-theta.aenv.site"
        rest_api.api_key = generate_random_string(64)
        rest_api.api_secret = generate_random_string(128)
        rest_api.status = "Active"
        rest_api.description = "You can make API calls from your application on above endpoint. Never share your API Secret with anyone."
        rest_api.save()
    return order


@login_required
def checkout_page(request):
    model_inference_id = request.GET['model_inference_id']
    service_name = request.GET['service_name']
    service_type = request.GET['service_type']
    amount = request.GET['amount']
    context = {
        'model_inference': models.ModelInference.objects.get(id=int(model_inference_id)),
        'service_name': service_name,
        'service_type': service_type,
        'amount': amount,
        'buying_user': request.user
    }
    return render(request, 'inference_portal/checkout.html', context)


@login_required
def check_tfuel_transaction(request):
    from web3 import Web3, AsyncWeb3
    model_inference_id = request.GET['model_inference_id']
    service_name = request.GET['service_name']
    service_type = request.GET['service_type']
    amount = request.GET['amount']
    model_inference = models.ModelInference.objects.get(id=int(model_inference_id))

    if not hasattr(model_inference.user, 'paymentaddress') or not hasattr(request.user, 'paymentaddress'):
        return HttpResponse('<div class="row text-center"><div class="col-md-6 offset-md-3"><div class="alert alert-danger alert-dismissible fade show" role="alert"> Oops, either you or seller do not have a TFUEL address! Try again later! <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button> </div></div></div>')

    to_address = model_inference.user.paymentaddress.tfuel_address
    from_address = request.user.paymentaddress.tfuel_address
    if to_address and from_address:
        try:
            # TODO: scan blockchain to see if transaction received
            w3 = Web3(Web3.HTTPProvider('https://eth-rpc-api-testnet.thetatoken.org/rpc'))
            _balance = w3.eth.get_balance(to_address)
            balance = float(w3.from_wei(_balance, 'ether'))
            if balance >= float(amount) + float(model_inference.user.paymentaddress.tfuel_balance):
                model_inference.user.paymentaddress.tfuel_balance = balance
                model_inference.user.paymentaddress.save()
                order = process_order(model_inference.id, service_name, service_type, amount, request.user)
                _payment_done = '<a href="/order_details/' + str(order.id) + '" class="btn btn-success btn-lg mb-5"><i class="bi bi-box-arrow-in-right"></i> Proceed Now</a>'
                return  HttpResponse('<div class="row text-center"><div class="col-md-6 offset-md-3"><div class="alert alert-info alert-dismissible fade show" role="alert"> Payment received! <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button> </div> ' + _payment_done + ' </div></div>')
            else:
                return  HttpResponse('<div class="row text-center"><div class="col-md-6 offset-md-3"><div class="alert alert-warning alert-dismissible fade show" role="alert"> No update, please check again in a while! <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button> </div></div></div>')
        except:
            pass
    return HttpResponse("Oops, you don't have a TFUEL address")


@login_required
def get_tfuel_balance(request):
    from web3 import Web3, AsyncWeb3
    payment_address = models.PaymentAddress.objects.filter(user=request.user).first()
    if payment_address.tfuel_address:
        try:
            w3 = Web3(Web3.HTTPProvider('https://eth-rpc-api-testnet.thetatoken.org/rpc'))
            _balance = w3.eth.get_balance(payment_address.tfuel_address)
            balance = float(w3.from_wei(_balance, 'ether'))
            payment_address.tfuel_balance = balance
            payment_address.save()
            return  HttpResponse("Total: %s" % str(payment_address.tfuel_balance))
        except:
            pass
    return HttpResponse("Oops, you don't have a TFUEL address")


@login_required
def dashboard(request):
    context = {}
    return render(request, 'inference_portal/dashboard.html', context)


@login_required
def payments(request):
    context = {}
    user = request.user
    payment_address, created = models.PaymentAddress.objects.get_or_create(user=user)

    sell_orders = models.OrderTransaction.objects.filter(seller=request.user)

    if request.method == 'POST':
        form = forms.PaymentAddressForm(request.POST, instance=payment_address)
        if form.is_valid():
            form.save()
            # Redirect to a success page or display a success message
    else:
        form = forms.PaymentAddressForm(instance=payment_address)
    return render(request, 'inference_portal/payments.html', {'form': form, 'payment_address': payment_address, 'sell_orders': sell_orders})


class InferenceAppListView(ListView):
    model = models.ModelInference
    template_name = 'inference_portal/inferenceapp_list.html'
    context_object_name = 'inference_apps'

    def get_queryset(self):
        return models.ModelInference.objects.filter(user=self.request.user).order_by('-id')


class InferenceAppCreateView(CreateView):
    model = models.ModelInference
    form_class = forms.ModelInferenceAppForm
    template_name = 'inference_portal/inferenceapp_form.html'
    success_url = '/model_inference_apps'

    def form_valid(self, form):
        form.instance.user = self.request.user
        repsonse = super().form_valid(form)
        if form.instance.release_as_web_app:
            form.instance.web_app_access_url = utils.build_web_app_instance(inference_endpoint=form.instance.inference_endpoint, 
                                                                            status=form.instance.status,
                                                                            category=form.instance.category, 
                                                                            name=form.instance.name, 
                                                                            web_app_price_per_use=form.instance.web_app_price_per_use)
        if form.instance.release_as_plugin and form.instance.list_of_plugins is not None:
            for plugin in form.instance.list_of_plugins.all():
                if plugin.name == "WordPress":
                    file_path = utils.build_wordpress_app_instance(inference_endpoint=form.instance.inference_endpoint, 
                                                                   status=form.instance.status,
                                                                   category=form.instance.category, 
                                                                   name=form.instance.name, 
                                                                   plugin_price_per_use=form.instance.plugin_price_per_use)
                    models.ModelInferencePlugin.objects.create(name=plugin.name, file_path=file_path, model_inference_id=form.instance.id)
            
                if plugin.name == "Chrome Extension":
                    file_path = utils.build_chrome_extension_app_instance(inference_endpoint=form.instance.inference_endpoint, 
                                                                          status=form.instance.status,
                                                                          category=form.instance.category, 
                                                                          name=form.instance.name, 
                                                                          plugin_price_per_use=form.instance.plugin_price_per_use)
                    models.ModelInferencePlugin.objects.create(name=plugin.name, file_path=file_path, model_inference_id=form.instance.id)
            
                if plugin.name == "Shopify":
                    file_path = utils.build_shopify_app_instance(inference_endpoint=form.instance.inference_endpoint, 
                                                                 status=form.instance.status,
                                                                 category=form.instance.category, 
                                                                 name=form.instance.name, 
                                                                 plugin_price_per_use=form.instance.plugin_price_per_use)
                    models.ModelInferencePlugin.objects.create(name=plugin.name, file_path=file_path, model_inference_id=form.instance.id)
            
                if plugin.name == "Salesforce App":
                    file_path = utils.build_salesforce_app_instance(inference_endpoint=form.instance.inference_endpoint, 
                                                                    status=form.instance.status,
                                                                    category=form.instance.category, 
                                                                    name=form.instance.name, 
                                                                    plugin_price_per_use=form.instance.plugin_price_per_use)
                    models.ModelInferencePlugin.objects.create(name=plugin.name, file_path=file_path, model_inference_id=form.instance.id)

        form.instance.save()
        return repsonse


class InferenceAppEditView(UpdateView):
    model = models.ModelInference
    form_class = forms.ModelInferenceAppForm
    template_name = 'inference_portal/inferenceapp_form.html'
    success_url = '/model_inference_apps'

    def form_valid(self, form):
        form.instance.user = self.request.user
        repsonse = super().form_valid(form)
        if form.instance.release_as_web_app:
            form.instance.web_app_access_url = utils.build_web_app_instance(inference_endpoint=form.instance.inference_endpoint, 
                                                                            status=form.instance.status,
                                                                            category=form.instance.category, 
                                                                            name=form.instance.name, 
                                                                            web_app_price_per_use=form.instance.web_app_price_per_use)
        if form.instance.release_as_plugin and form.instance.list_of_plugins is not None:
            for plugin in form.instance.list_of_plugins.all():
                if plugin.name == "WordPress":
                    file_path = utils.build_wordpress_app_instance(inference_endpoint=form.instance.inference_endpoint, 
                                                                   status=form.instance.status,
                                                                   category=form.instance.category, 
                                                                   name=form.instance.name, 
                                                                   plugin_price_per_use=form.instance.plugin_price_per_use)
                    exists = models.ModelInferencePlugin.objects.filter(name=plugin.name, model_inference_id=form.instance.id).first()
                    if not exists:
                        models.ModelInferencePlugin.objects.create(name=plugin.name, file_path=file_path, model_inference_id=form.instance.id)
                    else:
                        exists.file_path = file_path
                        exists.save()
            
                if plugin.name == "Chrome Extension":
                    file_path = utils.build_chrome_extension_app_instance(inference_endpoint=form.instance.inference_endpoint, 
                                                                          status=form.instance.status,
                                                                          category=form.instance.category, 
                                                                          name=form.instance.name, 
                                                                          plugin_price_per_use=form.instance.plugin_price_per_use)
                    exists = models.ModelInferencePlugin.objects.filter(name=plugin.name, model_inference_id=form.instance.id).first()
                    if not exists:
                        models.ModelInferencePlugin.objects.create(name=plugin.name, file_path=file_path, model_inference_id=form.instance.id)
                    else:
                        exists.file_path = file_path
                        exists.save()
            
                if plugin.name == "Shopify":
                    file_path = utils.build_shopify_app_instance(inference_endpoint=form.instance.inference_endpoint, 
                                                                 status=form.instance.status,
                                                                 category=form.instance.category, 
                                                                 name=form.instance.name, 
                                                                 plugin_price_per_use=form.instance.plugin_price_per_use)
                    exists = models.ModelInferencePlugin.objects.filter(name=plugin.name, model_inference_id=form.instance.id).first()
                    if not exists:
                        models.ModelInferencePlugin.objects.create(name=plugin.name, file_path=file_path, model_inference_id=form.instance.id)
                    else:
                        exists.file_path = file_path
                        exists.save()
            
                if plugin.name == "Salesforce App":
                    file_path = utils.build_salesforce_app_instance(inference_endpoint=form.instance.inference_endpoint, 
                                                                    status=form.instance.status,
                                                                    category=form.instance.category, 
                                                                    name=form.instance.name, 
                                                                    plugin_price_per_use=form.instance.plugin_price_per_use)
                    exists = models.ModelInferencePlugin.objects.filter(name=plugin.name, model_inference_id=form.instance.id).first()
                    if not exists:
                        models.ModelInferencePlugin.objects.create(name=plugin.name, file_path=file_path, model_inference_id=form.instance.id)
                    else:
                        exists.file_path = file_path
                        exists.save()

        form.instance.save()
        return repsonse


@login_required
def profile_settings(request):
    context = {}
    return render(request, 'inference_portal/profile_settings.html', context)


def registerUser(request):
    if request.method == 'POST':
        form = forms.RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            login(request, user)
            return redirect('dashboard')  # Change 'home' to your desired redirect URL
    else:
        form = forms.RegistrationForm()
    
    context = {'form': form}
    return render(request, 'inference_portal/register.html', context)


def favicon_ico(request):
    favicon_path = os.path.join(settings.BASE_DIR, 'static', 'favicon.ico')
    return serve(request, os.path.basename(favicon_path), os.path.dirname(favicon_path))


def loginUser(request):
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                if user.profile_type == 'developer':
                    return redirect('dashboard')
                if user.profile_type == 'user':
                    return redirect('explore_apps')
                return redirect('dashboard')
            else:
                form.add_error(None, "Email OR password is incorrect.")
    else:
        form = forms.LoginForm()
    
    context = {'form': form}
    return render(request, 'inference_portal/login.html', context)


def logoutUser(request):
    logout(request)
    return redirect('index')