let TRANSLATION_SERVER_API = `http://localhost:3000/translate`;

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

let $tlBox = $("<div> </div>").attr("id", "ctl-box")

function showAlert(text1, text2) {
    $tlBox.html(`<div>${text1}</div><br/>`)
    console.log(text1, text2)
    text2.split(" ").forEach(word => {
        let wikiWord = word.replaceAll("-", "").replaceAll("–", "").replace(/[^a-zÅÄÖ ]/gi, '')
        wikiWord = wikiWord.toLowerCase()
        let url = `https://en.wiktionary.org/wiki/${wikiWord}#Swedish`
        $tlBox.append(`<a target="_blank" href="${url}" style="color: blue;"> ${word} </a>`)
    })
    getCustomDialogBox().dialog( "open");
}

function getCustomDialogBox() {
    return $("#ctl-box");
}

async function test() {
    await waitUntil(() => location.toString().indexOf("/video/") > 0)

    if(!getCustomDialogBox().length) {
        $('body').append($tlBox);
        getCustomDialogBox().dialog({
            width: '40%',
            height: 500,
            close: function( event, ui ) {
                $("button[title=Spela]").click()
            }
        }).css({ fontSize: 'large'});
        $(".ui-front").css({zIndex: 10000})

        getCustomDialogBox().dialog( "close");
    }

    function getSubtitleContainer() {
        return $('div[class*="_video-player__text-tracks_"]');
    }

    await waitUntil(() => getSubtitleContainer().length > 0)

    let subtitleNode= (getSubtitleContainer())[0]

    let observer = new MutationObserver(function( mutations ) {
        mutations.forEach(function( mutation ) {
            var newNodes = mutation.addedNodes; // DOM NodeList
            if( newNodes !== null ) { // If there are new nodes added
                var $nodes = $( newNodes ); // jQuery set
                $nodes.each(function() {
                    var $node = $( this );
                    // if( $($node).attr( "class" ).indexOf("_video-player__text-tracks_") >= 0 ) {
                    let text = $($node).html();
                    text = $(text.replace(/<br\s*\/?>/gi,' ')).text()

                    // console.log($node, text)
                    // Pause and Translate
                    $("button[title=Pausa]").click()
                    fetch(`${TRANSLATION_SERVER_API}?q=${text}&src=${location}`, {mode: 'no-cors'})
                        .then(resp => resp.json())
                        .then(it => {
                            console.log(it);
                            showAlert(it.eng, text)
                        })
                    // }
                });
            }
        });
    });

    // Configuration of the observer:
    let config = {
        attributes: true,
        childList: true,
        characterData: true
    };

    // Pass in the target node, as well as the observer options
    observer.observe(subtitleNode, config);
}

test()