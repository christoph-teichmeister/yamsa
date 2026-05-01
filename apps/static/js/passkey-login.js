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

async function startPasskeyLogin() {
    if (!window.PublicKeyCredential) {
        showPasskeyLoginError(msg.browserUnsupported ?? "Your browser does not support passkeys.");
        return;
    }

    try {
        const beginResp = await fetch(window.passkeyAuthBeginUrl, { method: "GET" });
        if (!beginResp.ok) {
            showPasskeyLoginError(msg.startFailed ?? "Error starting passkey login.");
            return;
        }
        const options = await beginResp.json();

        let assertionData;
        try {
            assertionData = await get_credential(options);
        } catch (e) {
            if (e.name === "NotAllowedError") {
                showPasskeyLoginError(msg.userCanceled ?? "Login cancelled.");
            } else if (e.name === "TimeoutError") {
                showPasskeyLoginError(msg.timeout ?? "Timed out. Please try again.");
            } else {
                showPasskeyLoginError(msg.notRecognized ?? "Passkey not recognised.");
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
            showPasskeyLoginError(result.message || msg.authFailed || "Login failed.");
        }
    } catch (e) {
        showPasskeyLoginError(msg.unexpected ?? "An unexpected error occurred.");
    }
}

function showPasskeyLoginError(msg) {
    const el = document.getElementById("passkey-login-error");
    if (el) {
        el.textContent = msg;
        el.classList.remove("d-none");
    }
}
