import os
import zipfile
import random
import string

APP_FILES_ROOT = 's3'


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


def build_wordpress_app_instance(inference_endpoint, status, category, name, plugin_price_per_use):
    ## TODO: replace with real API KEY and API URL
    API_URL = inference_endpoint
    API_KEY = "API-KEY"
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

