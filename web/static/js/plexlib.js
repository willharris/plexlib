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

    function updateSection(section) {
        let div = document.getElementById('results');
        __makeRequest('GET', `/update/${section}/`)
            .then(function (data) {
                div.innerText = data;
            })
            .catch(function (error) {
                div.innerText = `Error updating section '${section}': ${error}`;
            });

        return false;
    }

    function newMediaInSection(section) {
        let div = document.getElementById('results');
        __makeRequest('GET', `/new-media/${section}/`)
            .then(function (data) {
                div.innerText = data;
            })
            .catch(function (error) {
                div.innerText = `Error finding new media in section '${section}': ${error}`;
            });

        return false;
    }

    return {
        newMediaInSection: newMediaInSection,
        updateSection: updateSection
    };

}());
