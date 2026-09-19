"use client";

import { useEffect, useState } from "react";

const API =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  (typeof window !== "undefined"
    ? `http://${window.location.hostname}:8000`
    : "http://localhost:8000");
    
export default function WhatsAppPage() {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
        setError(err.message || "Failed to load conversations");
      } finally {
        setLoading(false);
      }
    }

    loadConversations();
  }, []);

  if (loading) {
    return <div style={{ padding: 24 }}>Loading conversations...</div>;
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <h1>WhatsApp Conversations</h1>

      {conversations.length === 0 ? (
        <p>No WhatsApp conversations yet.</p>
      ) : (
        conversations.map((conversation) => (
          <div
            key={conversation.id}
            style={{
              border: "1px solid #ddd",
              borderRadius: 8,
              padding: 16,
              marginBottom: 12,
            }}
          >
            <strong>
              {conversation.contact_name ||
                conversation.wa_contact_id}
            </strong>

            <div>{conversation.wa_contact_id}</div>

            <div>
              Status: {conversation.status}
            </div>
          </div>
        ))
      )}
    </div>
  );
}