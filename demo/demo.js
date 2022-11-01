// import window from "global/window";

function getQueryStringValue (key) {
	return decodeURIComponent(window.location.search.replace(new RegExp("^(?:.*[&\\?]" + encodeURIComponent(key).replace(/[\.\+\*]/g, "\\$&") + "(?:\\=([^&]*))?)?.*$", "i"), "$1"));
}

// borrowed from https://gist.github.com/niyazpk/f8ac616f181f6042d1e0
function updateUrlParameter (uri, key, value) {
	// remove the hash part before operating on the uri
	var
		i = uri.indexOf('#'),
		hash = i === -1 ? '' : uri.substr(i)
		;

	uri = i === -1 ? uri : uri.substr(0, i);

	var
		re = new RegExp("([?&])" + key + "=.*?(&|$)", "i"),
		separator = uri.indexOf('?') !== -1 ? "&" : "?"
		;

	if (!value) {
		// remove key-value pair if value is empty
		uri = uri.replace(new RegExp("([?&]?)" + key + "=[^&]*", "i"), '');

		if (uri.slice(-1) === '?') {
			uri = uri.slice(0, -1);
		}
		// replace first occurrence of & by ? if no ? is present

		if (uri.indexOf('?') === -1) {
			uri = uri.replace(/&/, '?');
		}

	} else if (uri.match(re)) {
		uri = uri.replace(re, '$1' + key + "=" + value + '$2');
	} else {
		uri = uri + separator + key + "=" + value;
	}
	return uri + hash;
}

var
	lang = getQueryStringValue('lang') || 'en',
	stretching = getQueryStringValue('stretching') || 'auto',
	languageSelector = document.querySelector('select[name=lang]'),
	stretchingSelector = document.querySelector('select[name=stretching]'),
	sourcesSelector = document.querySelectorAll('select[name=sources]'),
	sourcesTotal = sourcesSelector.length
;

languageSelector.value = lang;
languageSelector.addEventListener('change', function () {
	window.location.href = updateUrlParameter(window.location.href, 'lang', languageSelector.value);
});
stretchingSelector.value = stretching;
stretchingSelector.addEventListener('change', function () {
	window.location.href = updateUrlParameter(window.location.href, 'stretching', stretchingSelector.value);
});

const waitUntil = (condition) => {
	return new Promise((resolve) => {
		let interval = setInterval(() => {
			if (!condition()) {
				return
			}
			clearInterval(interval)
			resolve()
		}, 100)
	})
};

function sleep (time) {
	return new Promise((resolve) => setTimeout(resolve, time));
}

window.isPlaying = false
document.addEventListener('keyup', event => {
	if (event.code === 'Space') {
		console.log('Space pressed')
		if(window.media) {
			isPlaying = !isPlaying
			if(isPlaying) {
				window.media.play()
			} else {
				window.media.pause()
			}
		}
		event.stopImmediatePropagation()
	}
})

for (var i = 0; i < sourcesTotal; i++) {
	sourcesSelector[i].addEventListener('change', function () {

		var
			media = this.closest('.players').querySelector('.mejs__container').id,
			player = mejs.players[media]
		;

		player.setSrc(this.value.replace('&amp;', '&'));
		player.load();
		if (!mejs.Features.isiOS && !mejs.Features.isAndroid) {
			player.play();
		}

		var renderer = document.getElementById(player.media.id + '-rendername');
		renderer.querySelector('.src').innerHTML = '<a href="' + this.value + '" target="_blank">' + this.value + '</a>';
		renderer.querySelector('.renderer').innerHTML = player.media.rendererName;
		renderer.querySelector('.error').innerHTML = '';

	});

	// These media types cannot play at all on iOS, so disabling them
	if (mejs.Features.isiOS) {
		sourcesSelector[i].querySelector('option[value^="rtmp"]').disabled = true;
		if (sourcesSelector[i].querySelector('option[value$="webm"]')) {
			sourcesSelector[i].querySelector('option[value$="webm"]').disabled = true;
		}
		if (sourcesSelector[i].querySelector('option[value$=".mpd"]')) {
			sourcesSelector[i].querySelector('option[value$=".mpd"]').disabled = true;
		}
		if (sourcesSelector[i].querySelector('option[value$=".ogg"]')) {
			sourcesSelector[i].querySelector('option[value$=".ogg"]').disabled = true;
		}
		if (sourcesSelector[i].querySelector('option[value$=".flv"]')) {
			sourcesSelector[i].querySelector('option[value*=".flv"]').disabled = true;
		}
	}
}

window.playedAudio = {}

function playSwedishAudio(text) {
	if(playedAudio[text]) {
		return
	}

	let entry = currentTrack.caption.entries.find(it => it.text === text)
	if (entry) {
		let audioBase64 = currentTrackAudio[entry.identifier + ""]
		window.media.pause()
		let audio = null
		try {
			audio = new Audio('data:audio/ogg;base64,' + audioBase64)
			audio.playbackRate = 0.75
			let numWords = text.split(" ").length
			audio.addEventListener("ended", async function () {

				// await sleep(3000 + (Math.pow(1.2, numWords))*1000)
				// window.media.play()
			});
			audio.play().catch(e => {
				console.log(e, "Couldn't play "+ audioBase64)
				window.media.play()
			})
		} catch (e) {
			console.log(e, "Couldn't play "+ audioBase64)
			window.media.play()
		}
		playedAudio[text] = true
	}
}
window.copyToClipboard = (text) => {
	navigator.clipboard.writeText(text).then(() => {
		// alert("Copied to clipboard");
	});
}
window.translate = (e) => {
	let text = e.target.textContent
	copyToClipboard(text)
	let url = `https://www.systran.net/en/translate/?source=sv&target=en&input=${text}&domain=Generic&owner=systran&size=&lang=en&type=systransoft.com_redirect_box&srcurl=https%3A%2F%2Fwww.systransoft.com%2F`
	$('iframe').attr("src", url)
}

document.addEventListener('DOMContentLoaded', function () {

	mejs.i18n.language(lang);

	var mediaElements = document.querySelectorAll('video, audio'), i, total = mediaElements.length;

	for (i = 0; i < total; i++) {
		new MediaElementPlayer(mediaElements[i], {
			startLanguage: 'sv',
			defaultSpeed: 1,
			speeds: ["0.5",  "1.0", "1.5"],
			captionTextPreprocessor:  function (text) {
				$("#subtitle").html('')
				let spans = text.split(" ").map(it => it.trim()).map(it => `<span onclick="window.translate(event)" style="cursor: pointer;">${it} </span>`)
				spans.forEach(span => $("#subtitle").append(span))

				playSwedishAudio(text);
				return text
			},
			stretching: stretching,
			features: ['playpause', 'current', 'progress', 'duration', 'tracks', 'volume', 'skipback','jumpforward','speed', 'fullscreen'],
			pluginPath: '../build/', //This is for Flash plugin
			success: function (media) {
				var renderer = document.getElementById(media.id + '-rendername');

				// Add events
				media.addEventListener('loadedmetadata', function () {
					var src = media.originalNode.getAttribute('src').replace('&amp;', '&');
					if (src !== null && src !== undefined) {
						renderer.querySelector('.src').innerHTML = '<a href="' + src + '" target="_blank">' + src + '</a>';
						renderer.querySelector('.renderer').innerHTML = media.rendererName;
						renderer.querySelector('.error').innerHTML = '';
					}
				});

				media.addEventListener('error', function (e) {
					renderer.querySelector('.error').innerHTML = '<strong>Error</strong>: ' + e.message;
				});

				media.addEventListener('captionschange', async function (e) {
					renderer.querySelector('.error').innerHTML = '<strong>captionschange</strong>: ' + e.message;
					window.currentTrack = e.detail

					let parts = currentTrack.caption.src.split('/')
					let srtName = parts[parts.length - 1]
					parts[parts.length - 1] = "audio_" + srtName.replaceAll(".srt", ".json")
					let resp = await fetch(parts.join('/'))
					window.currentTrackAudio = await resp.json()
				})

				// media.addEventListener('timeupdate', function (e) {
				// 	//start, stop, identifier, text
				// 	console.log(media.getCurrentTime())
				// })
				window.media = media
			}
		});
	}
});
