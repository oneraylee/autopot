export interface ApiSuccessResponse<T> {
  ok: true;
  data: T;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details: Record<string, unknown>[];
  type: string;
}

export interface ApiErrorResponse {
  ok: false;
  error: ApiErrorBody;
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;
