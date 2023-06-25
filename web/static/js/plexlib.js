/* exported PlexLib */

'use strict';

const PlexLib = (function () {

    function __makeRequest(protocol, url) {
        return new Promise(function (resolve, reject) {
            const xhr = new XMLHttpRequest();

            xhr.onload = function () {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(xhr.response);
                } else {
                    reject({
                        status: xhr.status,
                        statusText: xhr.statusText
                    });
                }
            };

            xhr.onerror = function () {
                reject({
                    status: -1,
                    statusText: `Request to ${url} failed!`
                });
            };

            xhr.open(protocol, url);
            xhr.send();
        });
    }

    function libraryAction(section, action) {
        let div = document.getElementById('results');
        __makeRequest('GET', `/${action}/${section}/`)
            .then(function (data) {
                div.innerText = data;
            })
            .catch(function (error) {
                div.innerText = `Error doing '${action}' in section '${section}': ${JSON.stringify(error)}`;
            });

        return false;
    }

    return {
        libraryAction: libraryAction
    };

}());
