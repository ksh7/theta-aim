import os
import zipfile
import random
import string

APP_FILES_ROOT = 's3'

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

def build_chrome_extension_app_instance(inference_endpoint, status, category, name, plugin_price_per_use):
    ## TODO: replace with real API KEY and API URL
    API_URL = inference_endpoint
    API_KEY = "API-KEY"
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
