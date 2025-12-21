const baseUrl = window.location.origin;
const url = new URL(window.location.href)
const token = url.searchParams.get("token")

async function verifyEmail() {
    try {
        const response = await fetch(`${baseUrl}/api/auth/verify?token=${token}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        })
        
        if (!response.ok) {
        throw new Error(`Ошибка ${response.status}`);
        }

        const data = await response.json();
        console.log("email confirmed:", data)

        document.getElementById("message").innerHTML = "<h1>Ваша почта успешна подтверждена!</h1><p>Теперь вы можете зайти на свой аккаунт :)</p>"
    } catch (error) {
            console.error("Ошибка при подтверждении:", error);
            document.getElementById("message").innerHTML = "<h1>Ошибка подтверждения</h1>";
    }
}

window.addEventListener("DOMContentLoaded", verifyEmail);
