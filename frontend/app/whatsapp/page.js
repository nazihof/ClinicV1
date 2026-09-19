"use client";

import { useEffect, useState } from "react";

const API =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  (typeof window !== "undefined"
    ? `http://${window.location.hostname}:8000`
    : "http://localhost:8000");

export default function WhatsAppPage() {

  // 1) PUT ALL useState LINES HERE
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);

  const [replyText, setReplyText] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState("");

  // 2) KEEP YOUR EXISTING useEffect HERE
  useEffect(() => {
    async function loadConversations() {
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("clinic_token")
          : null;

      if (!token) {
        setError("Not authenticated");
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(
          `${API}/whatsapp/conversations`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error(
            `Failed to load conversations (${response.status})`
          );
        }

        const data = await response.json();
        setConversations(data);

      } catch (err) {
        setError(
          err.message || "Failed to load conversations"
        );
      } finally {
        setLoading(false);
      }
    }

    loadConversations();
  }, []);


  // 3) PUT openConversation HERE
  // AFTER useEffect, BUT BEFORE return(...)
  async function openConversation(conversation) {
    setSelectedConversation(conversation);
    setMessagesLoading(true);

    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("clinic_token")
        : null;

    try {
      const response = await fetch(
        `${API}/whatsapp/conversations/${conversation.id}/messages`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          `Failed to load messages (${response.status})`
        );
      }

      const data = await response.json();
      setMessages(data);

    } catch (err) {
      console.error(err);

    } finally {
      setMessagesLoading(false);
    }
  }


  // 4) YOUR EXISTING LOADING / ERROR CHECKS
  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        Loading conversations...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <p>{error}</p>
      </div>
    );
  }
//send reply function
  async function sendReply() {
  if (!selectedConversation) return;

  const text = replyText.trim();

  if (!text) return;

  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("clinic_token")
      : null;

  if (!token) {
    setSendError("Not authenticated");
    return;
  }

  setSending(true);
  setSendError("");

  try {
    const response = await fetch(
      `${API}/whatsapp/send`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          phone_number_id:
            selectedConversation.phone_number_id,
          recipient:
            selectedConversation.wa_contact_id,
          message: text,
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      throw new Error(
        errorData.detail ||
          `Failed to send message (${response.status})`
      );
    }

    setReplyText("");

    await openConversation(selectedConversation);

  } catch (err) {
    setSendError(
      err.message || "Failed to send WhatsApp message"
    );

  } finally {
    setSending(false);
  }
}
  
  // 5) MAIN PAGE OUTPUT
  return (
    <div style={{ padding: 24 }}>

      <h1>WhatsApp Conversations</h1>

      {/* CONVERSATION LIST */}
      {conversations.length === 0 ? (
        <p>No WhatsApp conversations yet.</p>
      ) : (
        conversations.map((conversation) => (

          // 6) REPLACE YOUR OLD conversation DIV
          // WITH THIS CLICKABLE ONE
          <div
            key={conversation.id}
            onClick={() =>
              openConversation(conversation)
            }
            style={{
              border: "1px solid #ddd",
              borderRadius: 8,
              padding: 16,
              marginBottom: 12,
              cursor: "pointer",
            }}
          >
            <strong>
              {conversation.contact_name ||
                conversation.wa_contact_id}
            </strong>

            <div>
              {conversation.wa_contact_id}
            </div>

            <div>
              Status: {conversation.status}
            </div>
          </div>

        ))
      )}


      {/* 7) PUT MESSAGE HISTORY HERE */}
      {/* AFTER THE CONVERSATION LIST */}
    {selectedConversation && (
  <div style={{ marginTop: 20 }}>
    <textarea
      value={replyText}
      onChange={(e) => setReplyText(e.target.value)}
      placeholder="Type a WhatsApp reply..."
      rows={3}
      style={{
        width: "100%",
        padding: 12,
        borderRadius: 8,
        border: "1px solid #ccc",
      }}
    />

    {sendError && (
      <div
        style={{
          marginTop: 8,
          color: "red",
        }}
      >
        {sendError}
      </div>
    )}

    <button
      onClick={sendReply}
      disabled={sending || !replyText.trim()}
      style={{
        marginTop: 10,
        padding: "10px 18px",
        cursor: "pointer",
      }}
    >
      {sending ? "Sending..." : "Send Reply"}
    </button>
  </div>
)}   

    </div>
  );
}