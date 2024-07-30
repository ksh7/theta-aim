import os
import zipfile
import random
import string

APP_FILES_ROOT = 's3'

base_index_js = """
const express = require('express');
const { Shopify } = require('@shopify/shopify-api');
const dotenv = require('dotenv');
const shopifyRoutes = require('./routes/shopify');
const llmRoutes = require('./routes/llm');

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

Shopify.Context.initialize({
    API_KEY: process.env.SHOPIFY_API_KEY,
    API_SECRET_KEY: process.env.SHOPIFY_API_SECRET,
    SCOPES: process.env.SHOPIFY_SCOPES.split(','),
    HOST_NAME: `localhost:${port}`,
    API_VERSION: Shopify.Context.API_VERSIONS.JULY_2023,
    IS_EMBEDDED_APP: false,
});

app.use(express.json());
app.use('/shopify', shopifyRoutes);
app.use('/llm', llmRoutes);

app.listen(port, () => {
    console.log(`App is running on http://localhost:${port}`);
});


"""

base_shopify_js = """
const express = require('express');
const { Shopify } = require('@shopify/shopify-api');

const router = express.Router();

router.get('/auth', async (req, res) => {
    try {
        const authRoute = await Shopify.Auth.beginAuth(
            req,
            res,
            process.env.SHOPIFY_SHOP,
            '/shopify/callback',
            false
        );
        res.redirect(authRoute);
    } catch (error) {
        console.error(error);
        res.status(500).send('Error initiating Shopify auth');
    }
});

router.get('/callback', async (req, res) => {
    try {
        await Shopify.Auth.validateAuthCallback(req, res, req.query);
        res.redirect('/');
    } catch (error) {
        console.error(error);
        res.status(500).send('Error validating Shopify callback');
    }
});

module.exports = router;


"""

base_thetaaim_js = """
const express = require('express');
const axios = require('axios');

const router = express.Router();

router.post('/chat', async (req, res) => {
    const { message } = req.body;

    try {
        const response = await axios.post('https://test-api.theta-aim.com/api', {
            message,
            apiKey: process.env.LLM_API_KEY,
        });

        res.json(response.data);
    } catch (error) {
        console.error(error);
        res.status(500).send('Error communicating with LLM API');
    }
});

module.exports = router;


"""


def build_chrome_extension_app_instance(inference_endpoint, status, category, name, plugin_price_per_use):
    ## TODO: replace with real API KEY and API URL
    API_URL = inference_endpoint
    API_KEY = "API-KEY"

    index_filename = 'index.js'
    shopify_filename = 'shopify.js'
    thetallm_filename = 'llm.js'

    with open(index_filename, 'w') as _file:
        _file.write(base_index_js)

    with open(shopify_filename, 'w') as _file:
        _file.write(base_shopify_js)
    
    with open(thetallm_filename, 'w') as _file:
        _file.write(base_thetaaim_js)

    file_randomize = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    zip_filename = 'theta-ai-shopify-app-' + file_randomize + '.zip'

    if not os.path.exists(APP_FILES_ROOT):
        try:
            os.makedirs(APP_FILES_ROOT)
        except PermissionError:
            print(f"Permission denied: Cannot create directory {APP_FILES_ROOT}")
            return ""
    zip_file_path = APP_FILES_ROOT + '/' + zip_filename

    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        zipf.write(index_filename)
        zipf.write(shopify_filename)
        zipf.write(thetallm_filename)

    os.remove(index_filename)
    os.remove(shopify_filename)
    os.remove(thetallm_filename)

    return "app_files/" + zip_filename
