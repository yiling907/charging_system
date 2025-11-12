let backendbaseurl = "http://localhost:8080";
let apigatewaybaseurl = "http://localhost:4566/restapis/aarursynm0/v1/_user_request_/html/";

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

