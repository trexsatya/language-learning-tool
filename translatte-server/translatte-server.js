// const fsPromises = require('fs/promises');
// const fs = require('fs');
// const querystring = require('querystring');
// const languages = require('./languages.cjs');
// const proxy_check = require('proxy-check');
// const tunnel = require('tunnel');
// const got = require('got');
// const path = require('path');
// const express = require('express');
// const url = require('url');

import * as url from 'url'
import * as http from 'http'
import * as fsPromises from 'fs/promises';
import * as fs from 'fs';
import * as querystring from 'querystring';
// import * as languages from './languages.js';
import * as proxy_check from 'proxy-check';
import * as tunnel from 'tunnel';
import fetch from 'node-fetch'
// import Configstore from 'configstore';

// import * as got  from 'got';
import got from 'got'
import * as path from 'path';

console.log(got)

// import * as express from 'express';
// import * as bodyParser from 'body-parser';
// import * as url from 'url';

var langs = {
    'auto': 'Automatic',
    'af': 'Afrikaans',
    'sq': 'Albanian',
    'am': 'Amharic',
    'ar': 'Arabic',
    'hy': 'Armenian',
    'az': 'Azerbaijani',
    'eu': 'Basque',
    'be': 'Belarusian',
    'bn': 'Bengali',
    'bs': 'Bosnian',
    'bg': 'Bulgarian',
    'ca': 'Catalan',
    'ceb': 'Cebuano',
    'ny': 'Chichewa',
    'zh': 'Chinese (Simplified)',
    'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'co': 'Corsican',
    'hr': 'Croatian',
    'cs': 'Czech',
    'da': 'Danish',
    'nl': 'Dutch',
    'en': 'English',
    'eo': 'Esperanto',
    'et': 'Estonian',
    'tl': 'Filipino',
    'fi': 'Finnish',
    'fr': 'French',
    'fy': 'Frisian',
    'gl': 'Galician',
    'ka': 'Georgian',
    'de': 'German',
    'el': 'Greek',
    'gu': 'Gujarati',
    'ht': 'Haitian Creole',
    'ha': 'Hausa',
    'haw': 'Hawaiian',
    'he': 'Hebrew',
    'iw': 'Hebrew',
    'hi': 'Hindi',
    'hmn': 'Hmong',
    'hu': 'Hungarian',
    'is': 'Icelandic',
    'ig': 'Igbo',
    'id': 'Indonesian',
    'ga': 'Irish',
    'it': 'Italian',
    'ja': 'Japanese',
    'jw': 'Javanese',
    'kn': 'Kannada',
    'kk': 'Kazakh',
    'km': 'Khmer',
    'ko': 'Korean',
    'ku': 'Kurdish (Kurmanji)',
    'ky': 'Kyrgyz',
    'lo': 'Lao',
    'la': 'Latin',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'lb': 'Luxembourgish',
    'mk': 'Macedonian',
    'mg': 'Malagasy',
    'ms': 'Malay',
    'ml': 'Malayalam',
    'mt': 'Maltese',
    'mi': 'Maori',
    'mr': 'Marathi',
    'mn': 'Mongolian',
    'my': 'Myanmar (Burmese)',
    'ne': 'Nepali',
    'no': 'Norwegian',
    'ps': 'Pashto',
    'fa': 'Persian',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'pa': 'Punjabi',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sm': 'Samoan',
    'gd': 'Scots Gaelic',
    'sr': 'Serbian',
    'st': 'Sesotho',
    'sn': 'Shona',
    'sd': 'Sindhi',
    'si': 'Sinhala',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'so': 'Somali',
    'es': 'Spanish',
    'su': 'Sundanese',
    'sw': 'Swahili',
    'sv': 'Swedish',
    'tg': 'Tajik',
    'ta': 'Tamil',
    'te': 'Telugu',
    'th': 'Thai',
    'tr': 'Turkish',
    'uk': 'Ukrainian',
    'ur': 'Urdu',
    'uz': 'Uzbek',
    'vi': 'Vietnamese',
    'cy': 'Welsh',
    'xh': 'Xhosa',
    'yi': 'Yiddish',
    'yo': 'Yoruba',
    'zu': 'Zulu'
};
/**
 * Returns the ISO 639-1 code of the desiredLang – if it is supported by Google Translate
 * @param {string} desiredLang – the name or the code of the desired language
 * @returns {string|boolean} The ISO 639-1 code of the language or false if the language is not supported
 */
function getCode(desiredLang) {
    if (!desiredLang) {
        return false;
    }
    desiredLang = desiredLang.toLowerCase();

    if (langs[desiredLang]) {
        return desiredLang;
    }

    var keys = Object.keys(langs).filter(function (key) {
        if (typeof langs[key] !== 'string') {
            return false;
        }

        return langs[key].toLowerCase() === desiredLang;
    });

    return keys[0] || false;
}

/**
 * Returns true if the desiredLang is supported by Google Translate and false otherwise
 * @param desiredLang – the ISO 639-1 code or the name of the desired language
 * @returns {boolean}
 */
function isSupported(desiredLang) {
    return Boolean(getCode(desiredLang));
}

/**
 * Returns utf8 length
 * @param str – string
 * @returns {number}
 */
function utf8Length(str) {
    var utf8 = [];
    for (var i = 0; i < str.length; i++) {
        var charcode = str.charCodeAt(i);
        if (charcode < 0x80) utf8.push(charcode);
        else if (charcode < 0x800) {
            utf8.push(0xc0 | (charcode >> 6),
                0x80 | (charcode & 0x3f));
        } else if (charcode < 0xd800 || charcode >= 0xe000) {
            utf8.push(0xe0 | (charcode >> 12),
                0x80 | ((charcode >> 6) & 0x3f),
                0x80 | (charcode & 0x3f));
        }
        else {
            i++;
            charcode = 0x10000 + (((charcode & 0x3ff) << 10)
                | (str.charCodeAt(i) & 0x3ff));
            utf8.push(0xf0 | (charcode >> 18),
                0x80 | ((charcode >> 12) & 0x3f),
                0x80 | ((charcode >> 6) & 0x3f),
                0x80 | (charcode & 0x3f));
        }
    }
    return utf8.length;
}

function sM(a) {
    var b;
    if (null !== yr)
        b = yr;
    else {
        b = wr(String.fromCharCode(84));
        var c = wr(String.fromCharCode(75));
        b = [b(), b()];
        b[1] = c();
        b = (yr = window[b.join(c())] || "") || ""
    }
    var d = wr(String.fromCharCode(116))
        , c = wr(String.fromCharCode(107))
        , d = [d(), d()];
    d[1] = c();
    c = "&" + d.join("") + "=";
    d = b.split(".");
    b = Number(d[0]) || 0;
    for (var e = [], f = 0, g = 0; g < a.length; g++) {
        var l = a.charCodeAt(g);
        128 > l ? e[f++] = l : (2048 > l ? e[f++] = l >> 6 | 192 : (55296 === (l & 64512) && g + 1 < a.length && 56320 === (a.charCodeAt(g + 1) & 64512) ? (l = 65536 + ((l & 1023) << 10) + (a.charCodeAt(++g) & 1023),
            e[f++] = l >> 18 | 240,
            e[f++] = l >> 12 & 63 | 128) : e[f++] = l >> 12 | 224,
            e[f++] = l >> 6 & 63 | 128),
            e[f++] = l & 63 | 128)
    }
    a = b;
    for (f = 0; f < e.length; f++)
        a += e[f],
            a = xr(a, "+-a^+6");
    a = xr(a, "+-3^+b+-f");
    a ^= Number(d[1]) || 0;
    0 > a && (a = (a & 2147483647) + 2147483648);
    a %= 1E6;
    return c + (a.toString() + "." + (a ^ b))
}

var yr = null;
var wr = function (a) {
    return function () {
        return a
    }
}
    , xr = function (a, b) {
    for (var c = 0; c < b.length - 2; c += 3) {
        var d = b.charAt(c + 2)
            , d = "a" <= d ? d.charCodeAt(0) - 87 : Number(d)
            , d = "+" === b.charAt(c + 1) ? a >>> d : a << d;
        a = "+" === b.charAt(c) ? a + d & 4294967295 : a ^ d
    }
    return a
};

// END
/* eslint-enable */

// console.log(Configstore)

// var config = new Configstore('google-translate-api');

var window = {
    TKK: '422854.923862967'
};

function updateTKK(opts) {
    opts = opts || {tld: 'com', proxy: {}, headers: {}};
    return new Promise(function (resolve, reject) {
        var now = Math.floor(Date.now() / 3600000);

        if (Number(window.TKK.split('.')[0]) === now) {
            resolve();
        } else {
            got('https://translate.google.' + opts.tld, {...opts.proxy, headers: opts.headers, timeout: 2000, retry: 0}).then(function (res) {
                var code = res.body.match(/TKK='.*?';/g);

                if (code) {
                    eval(code[0]);
                    /* eslint-disable no-undef */
                    if (typeof TKK !== 'undefined') {
                        window.TKK = TKK;
                        // config.set('TKK', TKK);
                    }
                    /* eslint-enable no-undef */
                }

                /**
                 * Note: If the regex or the eval fail, there is no need to worry. The server will accept
                 * relatively old seeds.
                 */

                resolve();
            }).catch(function () {
                reject();
            });
        }
    });
}

function get(text, opts) {
    return updateTKK(opts).then(function () {
        var tk = sM(text);
        tk = tk.replace('&tk=', '');
        return {name: 'tk', value: tk};
    }).catch(function (e) {
        console.log(`Error  ${e}`)
        return null;
    });
}

const translatte = async (text, opts) => {
    opts = opts || {};
    opts = JSON.parse(JSON.stringify(opts));

    let result = {
        text: '',
        raw: '',
        from: {
            language: {
                didYouMean: false,
                iso: ''
            },
            text: {
                autoCorrected: false,
                value: '',
                didYouMean: false
            }
        },
        proxy: '',
        agent: '',
        service: {google_free: true}
    };

    let errors = [
        'The language «[lang]» is not supported',
        'Text must not exceed 5000 bytes',
        'The server returned an empty response',
        'Could not get token from google',
        'Text translation request failed'
    ];

    if (opts.from && !isSupported(opts.from)) {
        return Promise.reject({message: errors[0].replace('[lang]', opts.from)});
    }

    if (opts.to && !isSupported(opts.to)) {
        return Promise.reject({message: errors[0].replace('[lang]', opts.to)});
    }

    let bytes = utf8Length(text);
    opts.client = opts.client || 't';
    opts.tld = opts.tld || 'com';
    opts.from = getCode(opts.from || 'auto');
    opts.to = getCode(opts.to || 'en');
    opts.services = opts.services || {google_free: true};
    let services = Object.keys(opts.services);

    opts.priority = opts.priority
        ? typeof opts.priority === 'string'
            ? [opts.priority]
            : opts.priority.filter(p => services.indexOf(p) + 1)
        : services;

    if (opts.priority.length > 1) {
        let all_index = opts.priority.length - 1;
        let err_services = {};
        return opts.priority.reduce((p, priority, index) => {
            return p.then(prev => {
                return new Promise((resolve, reject) => {
                    if (prev) return resolve(prev);
                    translatte(text, {...opts, priority}).then(t => {
                        if (!t || !t.text) {
                            err_services[priority] = errors[2];
                            return all_index === index
                                ? reject(err_services)
                                : resolve();
                        }
                        return resolve(t);
                    }).catch(e => {
                        err_services[priority] = typeof e === 'object' && (e[priority] || e.message)
                            ? e[priority] || e.message
                            : e;
                        return all_index === index
                            ? reject(err_services)
                            : resolve();
                    });
                });
            });
        }, Promise.resolve());
    }

    let priority = opts.priority[0];

    if (bytes > 5000) {
        let chars = Math.ceil(text.length / Math.ceil(bytes / 4700)) + 100;
        let plain = ' ' + text + ' ';
        let texts = [];
        let j = 0;
        ['.', ',', ' '].forEach(separator => {
            if (!plain) return;
            let split = plain.split(separator);
            for (let i = 0, l = split.length; i < l; i++) {
                if (!texts[j]) texts[j] = [];
                if ((texts[j].join(separator) + split[i]).length < chars) {
                    texts[j].push(split[i]);
                    plain = split.slice(i+1).join(separator);
                } else {
                    if (!texts[j].length) break;
                    texts[j].push('');
                    texts[++j] = [];
                    if ((texts[j].join(separator) + split[i]).length < chars) {
                        texts[j].push(split[i]);
                        plain = split.slice(i+1).join(separator);
                    } else {
                        break;
                    }
                }
            }
            texts = texts.map(function (t) {
                if (!t) return;
                if (typeof t === 'object') {
                    return t.join(separator).trim();
                } else if (typeof t === 'string') {
                    return t.trim();
                }
            }).filter(Boolean);
        });
        if (!texts || !texts.length) return Promise.reject({[priority]: errors[1]});
        return texts.reduce((p, item) => {
            return p.then(prev => {
                return new Promise((resolve, reject) => {
                    setTimeout(() => {
                        translatte(item, opts).then(t => {
                            if (!t || !t.text) return reject(errors[2]);
                            t.text = prev && prev.text ? prev.text + ' ' + t.text : t.text;
                            return resolve(t);
                        }).catch(e => reject(e));
                    }, 1000);
                });
            });
        }, Promise.resolve());
    }

    if (priority === 'google_v3') {
        if (Array.isArray(opts.services['google_v3'])) {
            opts.services['google_v3'] = opts
                .services['google_v3'][Math.floor(Math.random() * opts
                .services['google_v3'].length)];
        }
        result.service = {google_v3: opts.services['google_v3']};
        let url = 'https://translation.googleapis.com/v3beta1/projects/' +
            opts.services['google_v3']['project-id'] + '/locations/global:translateText';
        try {
            const {body} = await got(url, {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + opts.services['google_v3']['token'],
                    'Content-type': 'application/json'
                },
                body: {
                    source_language_code: opts.from,
                    target_language_code: opts.to,
                    contents: [text]
                },
                json: true,
                timeout: 10000,
                retry: 0
            });
            for (const translation of body.translations) {
                result.text += result.text
                    ? ' ' + translation.translations.translatedText
                    : translation.translations.translatedText;
            }
        } catch (e) {
            return Promise.reject({google_v3: e.message || e});
        }
        return Promise.resolve(result);
    }

    if (priority === 'microsoft_v3') {
        if (!opts.services['microsoft_v3']) return Promise.resolve(result);
        if (Array.isArray(opts.services['microsoft_v3'])) {
            opts.services['microsoft_v3'] = opts
                .services['microsoft_v3'][Math.floor(Math.random() * opts
                .services['microsoft_v3'].length)];
        }
        result.service = {microsoft_v3: opts.services['microsoft_v3']};
        let url = 'https://api.cognitive.microsofttranslator.com/translate?' +
            querystring.stringify({
                'api-version': '3.0',
                from: opts.from === 'auto' ? '' : opts.from,
                to: opts.to
            });
        try {
            const {body} = await got(url, {
                method: 'POST',
                headers: {
                    'Ocp-Apim-Subscription-Key': opts.services['microsoft_v3']['key'],
                    'Ocp-Apim-Subscription-Region': opts.services['microsoft_v3']['location']
                        ? opts.services['microsoft_v3']['location'].replace(/[^a-z]/ig, '').toLowerCase()
                        : 'global',
                    'Content-type': 'application/json'
                },
                body: [{text}],
                json: true,
                timeout: 10000,
                retry: 0
            });
            for (const translation of body) {
                if (translation.detectedLanguage && translation.detectedLanguage.language) {
                    result.from.language.iso = translation.detectedLanguage.language;
                }
                result.text += result.text
                    ? ' ' + translation.translations[0].text
                    : translation.translations[0].text;
            }
        } catch (e) {
            return Promise.reject({microsoft_v3: e.message || e});
        }
        return Promise.resolve(result);
    }

    if (priority === 'yandex_v1') {
        if (!opts.services['yandex_v1']) return Promise.resolve(result);
        if (Array.isArray(opts.services['yandex_v1'])) {
            opts.services['yandex_v1'] = opts
                .services['yandex_v1'][Math.floor(Math.random() * opts
                .services['yandex_v1'].length)];
        }
        result.service = {yandex_v1: opts.services['yandex_v1']};
        let url = 'https://translate.yandex.net/api/v1.5/tr.json/translate?' +
            querystring.stringify({
                key: opts.services['yandex_v1']['key'],
                lang: opts.from && opts.from !== 'auto'
                    ? opts.from + '-' + opts.to
                    : opts.to,
                text: text
            });
        try {
            const {body} = await got(url, {json: true, timeout: 10000, retry: 0});
            for (const translation of body.text) {
                result.text += result.text
                    ? ' ' + translation
                    : translation;
            }
        } catch (e) {
            return Promise.reject({yandex_v1: e.message || e});
        }
        return Promise.resolve(result);
    }

    if (priority === 'yandex_v2') {
        if (!opts.services['yandex_v2']) return Promise.resolve(result);
        if (Array.isArray(opts.services['yandex_v2'])) {
            opts.services['yandex_v2'] = opts
                .services['yandex_v2'][Math.floor(Math.random() * opts
                .services['yandex_v2'].length)];
        }
        result.service = {yandex_v2: opts.services['yandex_v2']};
        let url = 'https://translate.api.cloud.yandex.net/translate/v2/translate';
        try {
            const {body} = await got(url, {
                method: 'POST',
                headers: {
                    'Authorization': 'Api-Key ' + opts.services['yandex_v2']['key'],
                    'Content-type': 'application/json'
                },
                body: {
                    sourceLanguageCode: opts.from,
                    targetLanguageCode: opts.to,
                    texts: [text]
                },
                json: true,
                timeout: 10000,
                retry: 0
            });
            for (const translation of body.translations) {
                result.text += result.text
                    ? ' ' + translation.text
                    : translation.text;
            }
        } catch (e) {
            return Promise.reject({yandex_v2: e.message || e});
        }
        return Promise.resolve(result);
    }

    let proxy = {};
    let translate = {};

    opts.agents = opts.agents
        ? typeof opts.agents === 'string'
            ? opts.agents.split(',').map(p => p.trim())
            : opts.agents
        : [];
    opts.proxies = opts.proxies
        ? typeof opts.proxies === 'string'
            ? opts.proxies.split(',').map(p => p.trim())
            : opts.proxies
        : [];

    if (opts.agents.length) {
        let a = opts.agents[Math.floor(Math.random() * opts.agents.length)];
        result.agent = a;
        opts.headers = {
            'User-Agent': a
        };
    }
    if (opts.proxies.length) {
        let p = opts.proxies[Math.floor(Math.random() * opts.proxies.length)];
        result.proxy = p;
        if (p.indexOf('@') + 1) {
            proxy.proxyAuth = p.split('@')[0];
            proxy.host = (p.split('@')[1]).split(':')[0];
            proxy.port = (p.split('@')[1]).split(':')[1];
        } else {
            proxy.host = p.split(':')[0];
            proxy.port = p.split(':')[1];
        }
    }

    opts.proxy = proxy.host
        ? opts.headers
            ? {agent: tunnel.httpsOverHttp({proxy, headers: opts.headers})}
            : {agent: tunnel.httpsOverHttp({proxy})}
        : {};

    const translate_string = () => {
        return new Promise(async (resolve, reject) => {
            let t = await get(text, opts);

            if (!t) return reject({google_free: errors[3]});

            let url = 'https://translate.google.' + opts.tld + '/translate_a/single?' +
                querystring.stringify({
                    [t.name]: t.value,
                    client: opts.client,
                    sl: opts.from,
                    tl: opts.to,
                    hl: opts.to,
                    dt: ['at', 'bd', 'ex', 'ld', 'md', 'qca', 'rw', 'rm', 'ss', 't'],
                    ie: 'UTF-8',
                    oe: 'UTF-8',
                    otf: 1,
                    ssel: 0,
                    tsel: 0,
                    kc: 7,
                    q: text
                });

            try {
                translate = await got(url, {...opts.proxy, json: true, timeout: 10000, headers: opts.headers, retry: 0});
            } catch (e) {
                return reject({google_free: errors[4]});
            }

            result.raw = opts.raw
                ? JSON.stringify(translate.body)
                : '';

            let body = translate.body;

            body[0].forEach(obj => {
                if (obj[0]) {
                    result.text += obj[0];
                }
            });

            if (body[2] === body[8][0][0]) {
                result.from.language.iso = body[2];
            } else {
                result.from.language.didYouMean = true;
                result.from.language.iso = body[8][0][0];
            }

            if (body[7] && body[7][0]) {
                let str = body[7][0];

                str = str.replace(/<b><i>/g, '[');
                str = str.replace(/<\/i><\/b>/g, ']');

                result.from.text.value = str;

                if (body[7][5] === true) {
                    result.from.text.autoCorrected = true;
                } else {
                    result.from.text.didYouMean = true;
                }
            }

            return result.text
                ? resolve(result)
                : reject({google_free: errors[2]});
        });
    };

    if (opts && opts.proxy && opts.proxy.agent) {
        return proxy_check(result.proxy).then(() => {
            return translate_string();
        }).catch(() => {
            return Promise.reject({google_free: result.proxy});
        });
    } else {
        return translate_string();
    }
};


// let app = express();
// app.use(express.json());

async function readFile(file, key) {
    try {
        const data = await fsPromises.readFile(file);
        return JSON.parse(data)
    } catch (e) {
        if(e.code === 'ENOENT') {
            let dir = path.dirname(file)
            console.log("File does not exist. Creating!", dir)

            if(!fs.existsSync(dir)) {
                fs.mkdirSync(dir, {recursive: true})
            }
            await fsPromises.appendFile(file, JSON.stringify({}));
            return {}
        }
    }
}

async function getTranslationFromServer(q) {
    console.log("Getting from server: ", q)
    return await translatte(q, {
        from: "sv",
        to: "en",
        agents: [
            'Mozilla/5.0 (Windows NT 10.0; ...',
            'Mozilla/4.0 (Windows NT 10.0; ...',
            'Mozilla/5.0 (Windows NT 10.0; ...'
        ],
        // proxies: [
        //     'LOGIN:PASSWORD@192.0.2.100:12345',
        //     'LOGIN:PASSWORD@192.0.2.200:54321'
        // ]
    });
}

function srcToLocalPath(src) {
    src = src.replace("https://", "").replace("http://", "")
    src = src.split("?")[0]
    src = src.replace("www.svtplay.se/video/", "svt/")
    if(src.indexOf("svt/") >= 0) {
        let splits = src.split("/")
        return `svt/${splits.slice(2).join("/")}`
    }
    return src
}

async function getFromLocalOrServer(q, src, ts, te, all) {
    src = src.toString()
    console.log("Src " + src)

    let localPath = "swedish/" + srcToLocalPath(src) + "/translation.json"

    let fileJson = await readFile(localPath);
    if(!fileJson || !fileJson.length) {
        console.log(`File ${localPath} doesn't exist or file is empty!`)
        fileJson = []
    }

    if(all) return fileJson

    let matching = fileJson.find(it => it['sv'] && it['sv'].trim() === q.trim())

    // console.log(fileJson, "fileJson")
    if(!matching) {
        let translation = await getTranslationFromServer(q)
        if(!translation.text) {
            return ''
        }
        matching = {sv: q.trim(), en: translation.text.trim(), ts: ts, te: te, id: fileJson.length + 1}
        fileJson.push(matching)

        console.log(`Translation fetched from server!`)
        await fsPromises.writeFile(localPath, JSON.stringify(fileJson))
    } else {
        console.log(`Translation found in file!`)
    }

    return matching['en']
}

// getFromLocalOrServer("hej", "https://www.svtplay.se/video/8Wv74NG/vagen-hem-berattelsen-om-en-adoption").then(data => {
//     console.log("data", data)
// })

const server = http.createServer(async (req, res) => {
    if (req.url.indexOf("/translate") >= 0 && req.method === "GET") {
        let reqUrl = new url.URL(`http://localhost${req.url}`)
        // console.log(reqUrl)
        let searchParams = reqUrl.searchParams
        let q = searchParams.get('q');
        let src = searchParams.get('src');
        let ts = searchParams.get('ts');
        let te = searchParams.get('te');
        let all = searchParams.get('all');

        try {
            let translated = await getFromLocalOrServer(q, src, ts, te, all)

            res.write(JSON.stringify({eng: translated }));
        } catch (e) {
            console.log(e)
            res.write(`{ "eng": "..." }\r\n`);
        }

        res.writeHead(200, { "Content-Type": "application/json" });
        //set the response

        //end the response
        res.end();
    } else {
        res.writeHead(404, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ message: "Route not found" }));
    }
});

// Function to handle the root path


let port = 3001;
server.listen(port, 'localhost',5, function() {
    console.log(`Server is listening on port ${port}`)
});

// module.exports = translatte;
// module.exports.languages = languages;