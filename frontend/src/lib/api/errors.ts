export class ApiError extends Error {
  readonly code: string;
  readonly type: string;
  readonly details: Record<string, unknown>[];

  constructor(
    code: string,
    message: string,
    type: string,
    details: Record<string, unknown>[] = [],
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.type = type;
    this.details = details;
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NetworkError";
  }
}
