import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { UserDetailView } from "./UserDetail";

const STORAGE_KEY = "coach.my_email";

/** The browser has no direct access to $CLAUDE_PLUGIN_DATA/coach/config.json
 * (that's a local filesystem path on the machine running Claude Code, not
 * something a static SPA can read) -- so identity here resolves from a
 * `?email=` query param first, falling back to whatever was saved in
 * localStorage from a previous visit. No admin controls are shown on this
 * route regardless of who's viewing it (see UserDetailView's
 * showAdminHint=false below). */
export function MyCoaching() {
  const [searchParams] = useSearchParams();
  const queryEmail = searchParams.get("email");
  const [email, setEmail] = useState(queryEmail ?? localStorage.getItem(STORAGE_KEY) ?? "");
  const [userId, setUserId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (queryEmail) {
      localStorage.setItem(STORAGE_KEY, queryEmail);
    }
  }, [queryEmail]);

  useEffect(() => {
    if (!email) return;
    setUserId(null);
    setError(null);
    api
      .getUserByEmail(email)
      .then((u) => {
        localStorage.setItem(STORAGE_KEY, email);
        setUserId(u.id);
      })
      .catch(() => setError("No coaching data found for that email yet."));
  }, [email]);

  if (!email || error) {
    return (
      <div className="card">
        <p className="section-title">Which email are you?</p>
        <p className="muted">
          This is the email `levelset` (or the automatic first-run default) saved for you locally.
        </p>
        {error && <p style={{ color: "var(--bad)" }}>{error}</p>}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const value = (e.currentTarget.elements.namedItem("email") as HTMLInputElement).value.trim();
            if (value) setEmail(value);
          }}
          style={{ display: "flex", gap: 8, marginTop: 8 }}
        >
          <input name="email" type="email" placeholder="you@example.com" defaultValue={email} />
          <button type="submit">View my coaching</button>
        </form>
      </div>
    );
  }

  if (!userId) return <div className="loading">Loading...</div>;

  return <UserDetailView userId={userId} showAdminHint={false} />;
}
