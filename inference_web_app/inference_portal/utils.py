import os
import zipfile
import random
import string
from web_app.settings import APP_FILES_ROOT


base_php_script = """
<?php
/*
Plugin Name: ThetaAIM AI Plugin
Description: A Theta EdgeCloud AI plugin that sends a request to an interference API and displays the response.
Version: 1.0
Author: ThetaAIM Team
*/

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

define('API_KEY', '{API_KEY}');

// Enqueue JavaScript
function taip_enqueue_scripts() {
    wp_enqueue_script('taip-script', plugins_url('taip-script.js', __FILE__), array('jquery'), '1.0', true);
    wp_localize_script('taip-script', 'taip_ajax_obj', array(
        'ajax_url' => admin_url('admin-ajax.php')
    ));
}
add_action('wp_enqueue_scripts', 'taip_enqueue_scripts');

// Add Shortcode
function taip_shortcode() {
    ob_start();
    ?>
    <form id="taip-form">
        <input type="text" id="taip-input" name="taip_input" placeholder="Enter something">
        <button type="submit">Submit</button>
    </form>
    <div id="taip-response"></div>
    <?php
    return ob_get_clean();
}
add_shortcode('taip_form', 'taip_shortcode');

// Handle AJAX Request
function taip_handle_ajax_request() {
    $input = sanitize_text_field($_POST['input']);

    // Replace with your external API URL
    $api_url = '{API_URL}?query=' . urlencode($input) . '&api_key=' . API_KEY;

    $response = wp_remote_get($api_url);

    if (is_wp_error($response)) {
        $error_message = $response->get_error_message();
        wp_send_json_error($error_message);
    } else {
        $body = wp_remote_retrieve_body($response);
        wp_send_json_success($body);
    }
}
add_action('wp_ajax_taip_handle_request', 'taip_handle_ajax_request');
add_action('wp_ajax_nopriv_taip_handle_request', 'taip_handle_ajax_request');
"""

base_php_jquery_script = """
jQuery(document).ready(function($) {
    $('#taip-form').on('submit', function(event) {
        event.preventDefault();

        var input = $('#taip-input').val();

        $.ajax({
            url: taip_ajax_obj.ajax_url,
            type: 'post',
            data: {
                action: 'taip_handle_request',
                input: input
            },
            success: function(response) {
                if (response.success) {
                    $('#taip-response').html('<p>' + response.data + '</p>');
                } else {
                    $('#taip-response').html('<p>Error: ' + response.data + '</p>');
                }
            }
        });
    });
});
"""


base_chrome_extension_manifest_script = """
{
  "manifest_version": 3,
  "name": "Theta AI GPT Extension",
  "version": "1.0",
  "description": "A Chrome extension for Theta AI with API integration.",
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "images/icon16.png",
      "48": "images/icon48.png",
      "128": "images/icon128.png"
    }
  },
  "permissions": [
    "storage",
    "activeTab"
  ]
}

"""

base_chrome_extension_popup_html_script = """
<!DOCTYPE html>
<html>
<head>
  <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" type="text/css" href="styles.css">
  <title>Theta AI Extension</title>
</head>
<body>
  <div class="container">
    <div class="chat-box" id="chat-box">
      <!-- Chat messages will appear here -->
    </div>
    <div class="input-group mb-3">
      <input type="text" class="form-control" id="query" placeholder="Type your message...">
      <div class="input-group-append">
        <button class="btn btn-primary" id="send-btn">Send</button>
      </div>
    </div>
  </div>
  <script src="popup.js"></script>
</body>
</html>

"""

base_chrome_extension_popup_js_script = """
document.addEventListener('DOMContentLoaded', function () {
  const chatBox = document.getElementById('chat-box');
  const queryInput = document.getElementById('query');
  const sendBtn = document.getElementById('send-btn');

  const apiKey = '{YOUR_API_KEY}';
  const apiEndpoint = '{YOUR_API_ENDPOINT}';

  sendBtn.addEventListener('click', function () {
    const query = queryInput.value;
    if (query) {
      sendMessage(query);
    }
  });

  function sendMessage(message) {
    displayMessage('You', message);

    fetch(apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({ query: message })
    })
    .then(response => response.json())
    .then(data => {
      displayMessage('Bot', data.response);
    })
    .catch(error => {
      console.error('Error:', error);
    });
  }

  function displayMessage(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message';
    messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
    chatBox.appendChild(messageElement);
    queryInput.value = '';
  }
});

"""


base_chrome_extension_styles_css_script = """
.container {
  padding: 20px;
}

.chat-box {
  height: 300px;
  overflow-y: auto;
  border: 1px solid #ccc;
  padding: 10px;
  margin-bottom: 10px;
}

.message {
  margin-bottom: 10px;
}

"""

def build_web_app_instance(inference_endpoint, status, category, name, web_app_price_per_use):
    ## TODO: for DEMO: currently just using a pre-deployed streamlit app
    ## eventually, we'll deploy app based on user submitted inference
    apps = {'Medical': 'https://medical-gpt-1.streamlit.app',
            'Finance': 'https://finance-gpt-1.streamlit.app',
            'Image': 'https://image-gpt-1.streamlit.app'}
    
    return apps[category]


def build_wordpress_app_instance(inference_endpoint, status, category, name, plugin_price_per_use):
    ## TODO: replace with real API KEY and API URL
    API_URL = inference_endpoint
    API_KEY = "TEST-API-KEY"
    updated_base_php_script = base_php_script.replace("{API_URL}", API_URL)
    updated_base_php_script = updated_base_php_script.replace("{API_KEY}", API_KEY)

    php_filename = 'theta-ai-plugin.php'
    js_filename = 'theta-ai-plugin.js'

    with open(php_filename, 'w') as php_file:
        php_file.write(updated_base_php_script)

    with open(js_filename, 'w') as js_file:
        js_file.write(base_php_jquery_script)

    file_randomize = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    zip_filename = 'theta-ai-plugin-' + file_randomize + '.zip'

    if not os.path.exists(APP_FILES_ROOT):
        try:
            os.makedirs(APP_FILES_ROOT)
        except PermissionError:
            print(f"Permission denied: Cannot create directory {APP_FILES_ROOT}")
            return ""
    zip_file_path = APP_FILES_ROOT + '/' + zip_filename

    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        zipf.write(php_filename)
        zipf.write(js_filename)

    os.remove(php_filename)
    os.remove(js_filename)

    return "app_files/" + zip_filename


def build_chrome_extension_app_instance(inference_endpoint, status, category, name, plugin_price_per_use):
    ## TODO: replace with real API KEY and API URL
    API_URL = inference_endpoint
    API_KEY = "TEST-API-KEY"
    updated_base_chrome_extension_popup_js_script = base_chrome_extension_popup_js_script.replace("{YOUR_API_ENDPOINT}", API_URL)
    updated_base_chrome_extension_popup_js_script = updated_base_chrome_extension_popup_js_script.replace("{YOUR_API_KEY}", API_KEY)

    manifest_filename = 'manifest.json'
    html_filename = 'popup.html'
    js_filename = 'popup.js'
    styles_filename = 'styles.css'

    with open(js_filename, 'w') as _file:
        _file.write(updated_base_chrome_extension_popup_js_script)

    with open(html_filename, 'w') as _file:
        _file.write(base_chrome_extension_popup_html_script)
    
    with open(manifest_filename, 'w') as _file:
        _file.write(base_chrome_extension_manifest_script)

    with open(styles_filename, 'w') as _file:
        _file.write(base_chrome_extension_styles_css_script)

    file_randomize = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    zip_filename = 'theta-ai-chrome-extension-' + file_randomize + '.zip'

    if not os.path.exists(APP_FILES_ROOT):
        try:
            os.makedirs(APP_FILES_ROOT)
        except PermissionError:
            print(f"Permission denied: Cannot create directory {APP_FILES_ROOT}")
            return ""
    zip_file_path = APP_FILES_ROOT + '/' + zip_filename

    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        zipf.write(js_filename)
        zipf.write(html_filename)
        zipf.write(manifest_filename)
        zipf.write(styles_filename)

    os.remove(js_filename)
    os.remove(html_filename)
    os.remove(manifest_filename)
    os.remove(styles_filename)

    return "app_files/" + zip_filename


def build_shopify_app_instance(inference_endpoint, status, category, name, plugin_price_per_use):
    ## TODO: replace with real zip file

    return "app_files/dummy/dummy_shopify_app.zip"


def build_salesforce_app_instance(inference_endpoint, status, category, name, plugin_price_per_use):
    ## TODO: replace with real zip file

    return "app_files/dummy/dummy_salesforce_app.zip"