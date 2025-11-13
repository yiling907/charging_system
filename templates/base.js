let backendbaseurl = "http://localhost:8080";
let apigatewaybaseurl = "https://v1wap266rf.execute-api.us-east-1.amazonaws.com/dev/html/";
let thirdpartapibaseurl="https://u1fpdf62ng.execute-api.us-east-1.amazonaws.com/Dev/"

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

