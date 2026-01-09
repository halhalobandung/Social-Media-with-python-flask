const socket = io();

const chatData = document.getElementById("chatData");
const myId = chatData.dataset.myid;
const targetId = chatData.dataset.targetid;

// PERBAIKAN: Gunakan parseInt agar ID dibaca sebagai angka
const room = parseInt(myId) < parseInt(targetId) 
    ? `${myId}_${targetId}` 
    : `${targetId}_${myId}`;

socket.emit("join", { room });

const sendBtn = document.getElementById("sendBtn");
const input = document.getElementById("messageInput");
const chatArea = document.getElementById("chatArea");

// Fungsi Kirim Pesan
function sendMessage() {
    const msg = input.value.trim();
    if (!msg) return;

    socket.emit("send_message", {
        room: room,
        message: msg,
        sender: myId,
        receiver: targetId
    });

    input.value = "";
    input.focus();
}

// Klik Tombol Kirim
sendBtn.onclick = sendMessage;

// Tekan Enter
input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
        e.preventDefault();
        sendMessage();
    }
});

// Terima Pesan
socket.on("receive_message", data => {
    const div = document.createElement("div");
    
    if (data.sender == myId) {
        div.className = "bubble me";
    } else {
        div.className = "bubble you";
    }
    
    div.innerText = data.message;
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
});