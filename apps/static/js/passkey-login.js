function getCsrfToken() {
    const name = "csrftoken";
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + "=")) {
            return decodeURIComponent(cookie.slice(name.length + 1));
        }
    }
    return null;
}

async function startPasskeyLogin() {
    if (!window.PublicKeyCredential) {
        showPasskeyLoginError("Dein Browser unterstützt keine Passkeys.");
        return;
    }

    try {
        const beginResp = await fetch(window.passkeyAuthBeginUrl, { method: "GET" });
        if (!beginResp.ok) {
            showPasskeyLoginError("Fehler beim Starten der Passkey-Anmeldung.");
            return;
        }
        const options = await beginResp.json();

        let assertionData;
        try {
            assertionData = await get_credential(options);
        } catch (e) {
            if (e.name === "NotAllowedError") {
                showPasskeyLoginError("Anmeldung abgebrochen.");
            } else if (e.name === "TimeoutError") {
                showPasskeyLoginError("Zeitüberschreitung. Bitte versuche es erneut.");
            } else {
                showPasskeyLoginError("Passkey nicht erkannt.");
            }
            return;
        }

        const formData = new FormData();
        formData.append("passkeys", JSON.stringify(assertionData.credential));
        formData.append("csrfmiddlewaretoken", getCsrfToken());

        const completeResp = await fetch(window.passkeyAuthCompleteUrl, {
            method: "POST",
            body: formData,
        });

        const result = await completeResp.json();
        if (result.status === "OK") {
            window.location.href = result.redirect;
        } else {
            showPasskeyLoginError(result.message || "Anmeldung fehlgeschlagen.");
        }
    } catch (e) {
        showPasskeyLoginError("Ein unerwarteter Fehler ist aufgetreten.");
    }
}

function showPasskeyLoginError(msg) {
    const el = document.getElementById("passkey-login-error");
    if (el) {
        el.textContent = msg;
        el.classList.remove("d-none");
    }
}
