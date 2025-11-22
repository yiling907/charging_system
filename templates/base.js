let backendbaseurl = "https://t0oy2j75f0.execute-api.us-east-1.amazonaws.com/dev/backend";
let apigatewaybaseurl = "https://t0oy2j75f0.execute-api.us-east-1.amazonaws.com/dev/html/";
let thirdpartapibaseurl = "https://7hzs4fjhzd.execute-api.us-east-1.amazonaws.com/dev/    "
let awsapibaseurl = "https://t0oy2j75f0.execute-api.us-east-1.amazonaws.com/dev/service_management"
let gatwaybaseurl = "https://t0oy2j75f0.execute-api.us-east-1.amazonaws.com/dev/"


function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) {
            return pair[1];
        }
    }
    return (false);
}


//=============================================================================
// Configuration
//=============================================================================

// The DOM element that the Google Pay button will be rendered into
const GPAY_BUTTON_CONTAINER_ID = 'createOrderBtn';

// Update the `merchantId` and `merchantName` properties with your own values.
// These fields are optional when the environment is `TEST`.
// Get your merchant Id at https://goo.gle/3Cmv497
const merchantInfo = {
    merchantId: '12345678901234567890',
    merchantName: 'Example Merchant',
};

/**
 * This is the base configuration for all Google Pay requests. This
 * configuration will be cloned, modified, and used for all Google Pay requests.
 *
 * @see {@link https://developers.google.com/pay/api/web/guides/test-and-deploy/integration-checklist}
 * @see {@link https://developers.google.com/pay/api/web/reference/request-objects}
 * @see {@link https://developers.google.com/pay/api/web/reference/request-objects#gateway}
 * @see {@link https://developers.google.com/pay/api/web/reference/request-objects#MerchantInfo}
 */
const baseGooglePayRequest = {
    apiVersion: 2,
    apiVersionMinor: 0,
    allowedPaymentMethods: [
        {
            type: 'CARD',
            parameters: {
                allowedAuthMethods: ['PAN_ONLY', 'CRYPTOGRAM_3DS'],
                allowedCardNetworks: ['AMEX', 'DISCOVER', 'INTERAC', 'JCB', 'MASTERCARD', 'VISA'],
            },
            tokenizationSpecification: {
                type: 'PAYMENT_GATEWAY',
                parameters: {
                    gateway: 'example',
                    gatewayMerchantId: 'exampleGatewayMerchantId',
                },
            },
        },
    ],
    merchantInfo,
};

// Prevent accidental edits to the base configuration. Mutations will be
// handled by cloning the config using deepCopy() and modifying the copy.
Object.freeze(baseGooglePayRequest);

//=============================================================================
// Google payments client singleton
//=============================================================================

/**
 * A variable to store the Google Payments Client instance.
 * Initialized to null to indicate it hasn't been created yet.
 */
let paymentsClient = null;

/**
 * Gets an instance of the Google Payments Client.
 *
 * This function ensures that only one instance of the Google Payments Client
 * is created and reused throughout the application. It lazily initializes
 * the client if it hasn't been created yet.
 *
 * @see {@link https://developers.google.com/pay/api/web/reference/client#PaymentsClient}
 * @return {google.payments.api.PaymentsClient} Google Payments Client instance.
 */
function getGooglePaymentsClient() {
    // Check if the paymentsClient has already been initialized.
    if (paymentsClient === null) {
        // If not, create a new instance of the Google Payments Client.
        paymentsClient = new google.payments.api.PaymentsClient({
            // Set the environment for the client ('TEST' or 'PRODUCTION').
            // `TEST` is default.
            environment: 'TEST',
            // Add the merchant information (optional)
            merchantInfo,
            paymentDataCallbacks: {
                onPaymentAuthorized: onPaymentAuthorized
            },
        });
    }

    return paymentsClient;
}

//=============================================================================
// Helpers
//=============================================================================

/**
 * Creates a deep copy of an object.
 *
 * This function uses JSON serialization and deserialization to create a deep
 * copy of the provided object. It's a convenient way to clone objects without
 * worrying about shared references.
 *
 * @param {Object} obj - The object to be copied.
 * @returns {Object} A deep copy of the original object.
 */
const deepCopy = obj => JSON.parse(JSON.stringify(obj));

/**
 * Renders the Google Pay button to the DOM.
 *
 * This function creates a Google Pay button using the Google Pay API and adds
 * it to the container element specified by `GPAY_BUTTON_CONTAINER_ID`.
 * When clicked, button triggers the `onGooglePaymentButtonClicked` handler.
 *
 * @see {@link https://developers.google.com/pay/api/web/reference/client#createButton}
 * @returns {void}
 */
function renderGooglePayButton() {
    // Create a Google Pay button using the PaymentsClient.
    const button = getGooglePaymentsClient().createButton({
        // Set the click handler for the button to the onGooglePaymentButtonClicked
        onClick: onGooglePaymentButtonClicked,
        // Set the allowed payment methods for the button.
        allowedPaymentMethods: baseGooglePayRequest.allowedPaymentMethods,
    });
    // Add the Google Pay button to the container element on the page.
    document.getElementById(GPAY_BUTTON_CONTAINER_ID).appendChild(button);
}

//=============================================================================
// Event Handlers
//=============================================================================

/**
 * Google Pay API loaded handler
 *
 * This function will be called by the script tag in index.html when the pay.js
 * script has finished loading. Once the script is loaded, it will first check
 * to see if the consumer is ready to pay with Google Pay. If they are ready,
 * the next thing it does is add the Google Pay button to the page. Otherwise,
 * it logs an error to the console.
 *
 * @see {@link https://developers.google.com/pay/api/web/reference/client#isReadyToPay}
 * @returns {void}
 */
function onGooglePayLoaded() {
    // Create a deep copy of the base Google Pay request object.
    // This ensures that any modifications made to the request object
    // do not affect the original base request.
    const req = deepCopy(baseGooglePayRequest);

    // Get an instance of the Google Payments Client.
    getGooglePaymentsClient()
        // Check if the user is ready to pay with Google Pay.
        .isReadyToPay(req)
        // Handle the response from the isReadyToPay() method.
        .then(function (res) {
            // If the user is ready to pay with Google Pay...
            if (res.result) {
                // Render the Google Pay button to the page.
                renderGooglePayButton();
            } else {
                // If the user is not ready to pay with Google Pay, log
                // an error to the console.
                console.log('Google Pay is not ready for this user.');
            }
        })
        // Handle any errors that occur during the process.
        .catch(console.error);
}

/**
 * Google Pay button click handler
 *
 * @see {@link https://developers.google.com/pay/api/web/reference/client#loadPaymentData}
 * @see {@link https://developers.google.com/pay/api/web/reference/response-objects#PaymentMethodTokenizationData}
 * @see {@link https://developers.google.com/pay/api/web/reference/request-objects#TransactionInfo}
 * @returns {void}
 */
function onGooglePaymentButtonClicked() {
    if (!isLoggedIn()) return;

    const selectedPackage = document.querySelector(`.package-item[data-id="${selectedPackageId}"]`);
    if (!selectedPackage) {
        alert('Please select a charging package');
        return;
    }
    // Create a new request data object for this request
    const req = {
        ...deepCopy(baseGooglePayRequest),
        transactionInfo: {
            countryCode: 'IE',
            currencyCode: 'EUR',
            totalPriceStatus: 'FINAL',
            totalPrice: Number(selectedPackage.dataset.price).toFixed(2),
        },
        callbackIntents: ['PAYMENT_AUTHORIZATION']
    };

    // Write the data to console for debugging
    console.log('onGooglePaymentButtonClicked', req);

    // Get an instance of the Google Payments Client.
    getGooglePaymentsClient()
        // Load the payment data in console for the transaction.
        .loadPaymentData(req)
        // If the payment is successful, process the payment
        .then(async function (res) {
            // show returned data for debugging
            console.log(res);
            // @todo pass payment token to your gateway to process payment
            // @note DO NOT save the payment credentials for future transactions,
            // unless they're used for merchant-initiated transactions with user
            // consent in place.
            paymentToken = res.paymentMethodData.tokenizationData.token;

            console.log(paymentToken)
            try {
                const now = new Date();
                let futureDate = new Date(now);
                futureDate.setHours(now.getHours() + Number(selectedPackage.dataset.time));
                const response = await axios.post(backendbaseurl + '/api/charging/records/', {
                    start_time: formatTime(now),
                    end_time: formatTime(futureDate),
                    electricity: "220",
                    charger: getChargerId(),
                    fee: Number(selectedPackage.dataset.price),
                    user: localStorage.getItem('userId')
                });
                console.log(response)
                const data = await response.data;
                console.log(data)
                const response_lambda = await axios.post(
                    awsapibaseurl + '/orders/',
                    {
                        paymentToken: paymentToken,
                        chargingTime: 1,
                        recordId: data.id,
                        chargerId: getChargerId()
                    }
                );

                if (response_lambda.statusCode === 200) {
                    alert('Payment successful! Redirecting to order list...');
                    window.location.href = apigatewaybaseurl + 'chargerRecord.html';
                    return resolve({transactionState: 'SUCCESS'});
                } else {
                    throw new Error(response.data.message || 'Payment failed');
                }

                alert('Order created successfully! Redirecting to order list soon');
                window.location.href = apigatewaybaseurl + `chargerRecord.html`;

            } catch (err) {
                const errorMsg = err.response?.data?.message || err.message || 'Payment processing failed';
                alert('Payment failed: ' + errorMsg);

            }
        })
        // If there is an error, log it to the console.
        .catch(console.error);
}

function onPaymentAuthorized(paymentData) {
    return new Promise(function (resolve, reject) {
        // Write the data to console for debugging
        console.log('onPaymentAuthorized', paymentData);

        // Do something here to pass token to your gateway

        // To simulate the payment processing, there is a 70% chance of success
        const paymentAuthorizationResult =
            Math.random() > 0.3
                ? {transactionState: 'SUCCESS'}
                : {
                    transactionState: 'ERROR',
                    error: {
                        intent: 'PAYMENT_AUTHORIZATION',
                        message: 'Insufficient funds',
                        reason: 'PAYMENT_DATA_INVALID',
                    },
                };
        resolve(paymentAuthorizationResult);
    });
}
