export default function DataDeletionPage() {
  return (
    <main
      style={{
        maxWidth: "900px",
        margin: "0 auto",
        padding: "40px 20px",
        lineHeight: "1.7",
        color: "#2b2b2b",
      }}
    >
      <div
        style={{
          background: "#ffffff",
          padding: "40px",
          borderRadius: "10px",
          boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
        }}
      >
        <h1>Data Deletion Instructions</h1>

        <p>
          <em>Last updated: October 2026</em>
        </p>

        <p>
          Clinic FrontDesk allows users and patients to request deletion of
          personal information associated with the platform.
        </p>

        <h2>How to Request Data Deletion</h2>

        <ol>
          <li>
            If you are a patient, first contact the clinic with which you have
            an appointment and request deletion or correction of your
            information.
          </li>

          <li>
            If your request relates to Clinic FrontDesk itself, send an email
            to <strong>rawinazih@gmail.com</strong>.
          </li>

          <li>
            Include enough information for us to identify the relevant record,
            such as your name, phone number, clinic name, and a short
            description of your request.
          </li>

          <li>
            We may need to verify your identity before processing the request
            in order to protect patient information from unauthorized deletion
            requests.
          </li>
        </ol>

        <h2>What May Be Deleted</h2>

        <ul>
          <li>Patient contact information stored in Clinic FrontDesk.</li>
          <li>
            Appointment-related records where deletion is appropriate.
          </li>
          <li>WhatsApp message records stored by Clinic FrontDesk.</li>
          <li>
            Other personal information associated with the user or patient.
          </li>
        </ul>

        <h2>Information That May Be Retained</h2>

        <p>
          Some information may be retained where necessary for security,
          fraud prevention, audit requirements, legal obligations, dispute
          resolution, or legitimate clinic record-keeping requirements.
          Where possible, retained data may be minimized or de-identified.
        </p>

        <h2>Processing Time</h2>

        <p>
          We will review deletion requests within a reasonable period and
          communicate the outcome or any additional information needed to
          process the request.
        </p>

        <h2>Contact</h2>

        <p>
          For data deletion requests, contact:
          <br />
          <strong>REPLACE_WITH_YOUR_REAL_EMAIL</strong>
        </p>

        <hr style={{ marginTop: "40px", borderColor: "#eceff3" }} />

        <p style={{ color: "#666", fontSize: "0.92rem" }}>
          Clinic FrontDesk — Data Deletion Instructions
        </p>
      </div>
    </main>
  );
}