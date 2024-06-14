const sources = ["ORTM", "Malijet", "Maliweb", "aBamako"];
let currentIndex = 0;
const changingText = document.getElementById('changing-text');
const cursor = document.querySelector('.blinking-cursor');

function typeText(text, callback) {
    let index = 0;
    function type() {
        if (index < text.length) {
            changingText.textContent += text[index];
            index++;
            setTimeout(type, 100);
        } else {
            setTimeout(callback, 2000);
        }
    }
    type();
}

function eraseText(callback) {
    let text = changingText.textContent;
    function erase() {
        if (text.length > 0) {
            text = text.slice(0, -1);
            changingText.textContent = text;
            setTimeout(erase, 50);
        } else {
            setTimeout(callback, 500);
        }
    }
    erase();
}

function cycleText() {
    if (currentIndex < sources.length - 1) {
        eraseText(() => {
            currentIndex++;
            typeText(sources[currentIndex], cycleText);
        });
    } else {
        eraseText(() => {
            currentIndex = 0;
            typeText(sources[currentIndex], () => {
                cursor.style.display = 'none'; // Hide the cursor after the last text is typed
            });
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    typeText(sources[currentIndex], cycleText);
});

// Set current year
document.getElementById('current-year').textContent = new Date().getFullYear();
