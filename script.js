async function analyzeVideo() {

    const url = document.getElementById("youtubeLink").value.trim();

    if (url === "") {
        alert("Please paste a YouTube URL.");
        return;
    }

    document.getElementById("loading").style.display = "block";

    try {

        const response = await fetch("http://127.0.0.1:5000/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                youtube_url: url
            })
        });

        if (!response.ok) {
            throw new Error("Backend returned " + response.status);
        }

        const data = await response.json();

        document.getElementById("loading").style.display = "none";

        if (data.status !== "success") {
            alert(data.message);
            return;
        }

        localStorage.setItem("focusclipData", JSON.stringify(data));

        window.location.href = "speakers.html";

    } catch (error) {

        document.getElementById("loading").style.display = "none";

        alert("Error:\n\n" + error.message);

        console.error(error);

    }

}