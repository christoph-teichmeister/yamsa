function getCsrfToken() {
    if (window.csrfToken) {
        return window.csrfToken;
    }
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

async function beginPasskeyRegistration(keyName) {
    if (!window.PublicKeyCredential) {
        showPasskeyRegError("Dein Browser unterstützt keine Passkeys.");
        return;
    }

    if (!keyName || keyName.trim() === "") {
        showPasskeyRegError("Bitte gib einen Namen für deinen Passkey ein.");
        return;
    }

    try {
        const beginResp = await fetch(window.passkeyRegBeginUrl, { method: "GET" });
        if (!beginResp.ok) {
            const data = await beginResp.json();
            showPasskeyRegError(data.message || "Fehler beim Starten der Registrierung.");
            return;
        }
        const options = await beginResp.json();

        let credential;
        try {
            credential = await get_new_credentials(options);
        } catch (e) {
            if (e.name === "NotAllowedError") {
                showPasskeyRegError("Registrierung abgebrochen.");
            } else {
                showPasskeyRegError("Passkey konnte nicht erstellt werden.");
            }
            return;
        }

        credential["key_name"] = keyName.trim();

        const completeResp = await fetch(window.passkeyRegCompleteUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify(credential),
        });

        const result = await completeResp.json();
        if (result.status === "OK") {
            window.location.reload();
        } else {
            showPasskeyRegError(result.message || "Registrierung fehlgeschlagen.");
        }
    } catch (e) {
        showPasskeyRegError("Ein unerwarteter Fehler ist aufgetreten.");
    }
}

function showPasskeyRegError(msg) {
    const el = document.getElementById("passkey-reg-result");
    if (el) {
        el.textContent = msg;
        el.classList.remove("d-none");
    }
}
