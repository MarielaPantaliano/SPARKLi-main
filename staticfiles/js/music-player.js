document.addEventListener("DOMContentLoaded", function() {
    const audio = document.getElementById("game-bg-music");
    const toggleButton = document.getElementById("toggle-music");

    const musicState = localStorage.getItem("musicState");
    if (musicState === "on") {
        const currentTime = sessionStorage.getItem("currentTime");
        if (currentTime) {
            audio.currentTime = parseFloat(currentTime);
        }
        audio.play().catch(error => {
            console.log('Autoplay failed:', error);
        });
    }

    function toggleMusic() {
        if (audio.paused) {
            audio.play();
            localStorage.setItem("musicState", "on"); 
        } else {
            audio.pause();
            localStorage.setItem("musicState", "off"); 
        }
    }

    toggleButton.addEventListener("click", toggleMusic);

    window.addEventListener("beforeunload", function() {
        sessionStorage.setItem("currentTime", audio.currentTime);
    });
});
