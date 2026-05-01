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

const msg = window.passkeyMessages || {};

async function beginPasskeyRegistration(keyName) {
    if (!window.PublicKeyCredential) {
        showPasskeyRegError(msg.browserUnsupported ?? "Your browser does not support passkeys.");
        return;
    }

    if (!keyName || keyName.trim() === "") {
        showPasskeyRegError(msg.nameRequired ?? "Please enter a name for your passkey.");
        return;
    }

    try {
        const beginResp = await fetch(window.passkeyRegBeginUrl, { method: "GET" });
        if (!beginResp.ok) {
            const data = await beginResp.json();
            showPasskeyRegError(data.message || msg.startFailed || "Error starting registration.");
            return;
        }
        const options = await beginResp.json();

        let credential;
        try {
            credential = await get_new_credentials(options);
        } catch (e) {
            if (e.name === "NotAllowedError") {
                showPasskeyRegError(msg.userCanceled ?? "Registration cancelled.");
            } else {
                showPasskeyRegError(msg.createFailed ?? "Passkey could not be created.");
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
            showPasskeyRegError(result.message || msg.registrationFailed || "Registration failed.");
        }
    } catch (e) {
        showPasskeyRegError(msg.unexpected ?? "An unexpected error occurred.");
    }
}

function showPasskeyRegError(msg) {
    const el = document.getElementById("passkey-reg-result");
    if (el) {
        el.textContent = msg;
        el.classList.remove("d-none");
    }
}
