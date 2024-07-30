import os
import zipfile
import random
import string

APP_FILES_ROOT = 's3'

base_apex_class = """
public class LLMChatService {
    private static final String API_URL = 'https://test-api.theta-aim.com/v1/chat';
    private static final String API_KEY = 'YOUR_API_KEY';

    public class ChatResponse {
        public String message;
    }

    @AuraEnabled
    public static String sendMessage(String userMessage) {
        Http http = new Http();
        HttpRequest request = new HttpRequest();
        request.setEndpoint(API_URL);
        request.setMethod('POST');
        request.setHeader('Content-Type', 'application/json');
        request.setHeader('Authorization', 'Bearer ' + API_KEY);

        String requestBody = '{"message": "' + userMessage + '"}';
        request.setBody(requestBody);

        try {
            HttpResponse response = http.send(request);
            if (response.getStatusCode() == 200) {
                ChatResponse chatResponse = (ChatResponse) JSON.deserialize(response.getBody(), ChatResponse.class);
                return chatResponse.message;
            } else {
                return 'Error: ' + response.getStatusCode();
            }
        } catch (Exception e) {
            return 'Error: ' + e.getMessage();
        }
    }
}


"""

base_app_html = """
<!-- llmChat.html -->
<template>
    <lightning-card title="Chat with LLM">
        <div class="slds-p-around_medium">
            <lightning-textarea label="Your Message" value={userMessage} onchange={handleInputChange}></lightning-textarea>
            <lightning-button label="Send" onclick={handleSendMessage} class="slds-m-top_medium"></lightning-button>
            <template if:true={responseMessage}>
                <lightning-card title="Response" class="slds-m-top_medium">
                    <p>{responseMessage}</p>
                </lightning-card>
            </template>
        </div>
    </lightning-card>
</template>

"""

base_thetaaim_js = """
import { LightningElement, track } from 'lwc';
import sendMessage from '@salesforce/apex/LLMChatService.sendMessage';

export default class LlmChat extends LightningElement {
    @track userMessage = '';
    @track responseMessage = '';

    handleInputChange(event) {
        this.userMessage = event.target.value;
    }

    handleSendMessage() {
        sendMessage({ userMessage: this.userMessage })
            .then(result => {
                this.responseMessage = result;
            })
            .catch(error => {
                this.responseMessage = 'Error: ' + error.body.message;
            });
    }
}

"""

base_thetaaim_xml = """
<!-- llmChat.js-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>52.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__AppPage</target>
        <target>lightning__RecordPage</target>
        <target>lightning__HomePage</target>
    </targets>
</LightningComponentBundle>

"""


def build_chrome_extension_app_instance(inference_endpoint, status, category, name, plugin_price_per_use):
    ## TODO: replace with real API KEY and API URL
    API_URL = inference_endpoint
    API_KEY = "API-KEY"

    salesforce_apex_filename = 'apex'
    salesforce_html_filename = 'theta-app.html'
    salesforce_js_filename = 'theta-app.js'
    salesforce_xml_filename = 'theta-app.xml'

    with open(salesforce_apex_filename, 'w') as _file:
        _file.write(base_apex_class)

    with open(salesforce_html_filename, 'w') as _file:
        _file.write(base_app_html)
    
    with open(salesforce_js_filename, 'w') as _file:
        _file.write(base_thetaaim_js)
    
    with open(salesforce_xml_filename, 'w') as _file:
        _file.write(base_thetaaim_xml)

    file_randomize = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    zip_filename = 'theta-ai-salesforce-app-' + file_randomize + '.zip'

    if not os.path.exists(APP_FILES_ROOT):
        try:
            os.makedirs(APP_FILES_ROOT)
        except PermissionError:
            print(f"Permission denied: Cannot create directory {APP_FILES_ROOT}")
            return ""
    zip_file_path = APP_FILES_ROOT + '/' + zip_filename

    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        zipf.write(salesforce_apex_filename)
        zipf.write(salesforce_html_filename)
        zipf.write(salesforce_js_filename)
        zipf.write(salesforce_xml_filename)

    os.remove(salesforce_apex_filename)
    os.remove(salesforce_html_filename)
    os.remove(salesforce_js_filename)
    os.remove(salesforce_xml_filename)

    return "app_files/" + zip_filename
