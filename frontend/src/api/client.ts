const DEFAULT_BASE_URL = "http://localhost:8000";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE_URL;

interface RequestOptions extends RequestInit {
  parseJson?: boolean;
}

async function parseErrorMessage(response: Response) {
  try {
    const data = await response.json();
    if (data?.detail) {
      return String(data.detail);
    }
  } catch {
    // JSON 파싱 실패 시 기본 메시지 사용
  }
  return `요청에 실패했습니다. (HTTP ${response.status})`;
}

export async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { parseJson = true, ...init } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
    ...init,
  });

  if (!response.ok) {
    const message = await parseErrorMessage(response);
    throw new Error(message);
  }

  if (!parseJson) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
