$(document).ready(function () {
  // Display speak/status message on the SiriWave screen
  eel.expose(DisplayMessage);
  function DisplayMessage(message) {
    $(".siri-message li:first").text(message);
    $(".siri-message").textillate("start");
  }

  // ShowHood — return to the idle start page (blue sphere)
  // ONLY called when user explicitly closes or on fatal shutdown
  eel.expose(ShowHood);
  function ShowHood() {
    $("#Oval").attr("hidden", false);
    $("#SiriWave").attr("hidden", true); // Bug fix: was "#Siriwave" (wrong case)
  }

  // KeepListening — stay on the SiriWave page (don't go back to start)
  // Used for continuous conversation: after one command, Jarvis stays listening
  eel.expose(KeepListening);
  function KeepListening() {
    // Ensure we're still on the SiriWave (listening) page
    $("#Oval").attr("hidden", true);
    $("#SiriWave").attr("hidden", false);
  }

  // Chat message display
  eel.expose(senderText);
  function senderText(message) {
    var chatBox = document.getElementById("chat-canvas-body");
    if (message.trim() !== "") {
      chatBox.innerHTML += `<div class="row justify-content-end mb-4">
            <div class = "width-size">
            <div class="sender_message">${message}</div>
        </div>`;
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  }

  eel.expose(receiverText);
  function receiverText(message) {
    var chatBox = document.getElementById("chat-canvas-body");
    if (message.trim() !== "") {
      chatBox.innerHTML += `<div class="row justify-content-start mb-4">
            <div class = "width-size">
            <div class="receiver_message">${message}</div>
            </div>
        </div>`;
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  }
});
