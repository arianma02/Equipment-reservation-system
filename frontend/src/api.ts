export const SESSION_ENDED = "session-ended";
export const SESSION_MESSAGE = "Your session has ended. Please log in again.";

// Callers retain their existing response parsing. Only authenticated failures
// invalidate a session; a role-related 403 must not log a valid user out.
export async function apiFetch(input: RequestInfo | URL, init?: RequestInit) {
  const headers = new Headers(init?.headers);
  const requestToken = headers.get("Authorization");
  const response = await fetch(input, init);
  let disabled = false;
  if (response.status === 403 && requestToken) {
    const body = await response
      .clone()
      .json()
      .catch(() => null);
    disabled = body?.detail === "Account is disabled";
  }
  if (requestToken && (response.status === 401 || disabled)) {
    // An old request must not clear a newer login.
    if (requestToken === `Bearer ${localStorage.getItem("access_token")}`) {
      localStorage.removeItem("access_token");
      window.dispatchEvent(new Event(SESSION_ENDED));
    }
    throw new Error(SESSION_MESSAGE);
  }
  return response;
}
