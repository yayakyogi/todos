// Client for the todos API (api/app/routers/todos.py).
// Requests go to /api, which the Vite dev server or nginx forwards to the API.

export type TodoStatus = 'open' | 'completed';

// Mirrors TodoResponse in api/app/schemas/todo.py
export interface Todo {
	id: string;
	title: string;
	description: string | null;
	status: TodoStatus;
	due_date: string | null;
	completed_at: string | null;
	created_at: string;
	updated_at: string;
}

// Mirrors TodoCreate
export interface TodoCreate {
	title: string;
	description?: string | null;
	due_date?: string | null;
}

// Mirrors TodoUpdate
export type TodoUpdate = Partial<Pick<Todo, 'title' | 'description' | 'status' | 'due_date'>>;

const BASE_URL = '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const response = await fetch(`${BASE_URL}${path}`, {
		...init,
		headers: { 'Content-Type': 'application/json', ...init?.headers }
	});
	if (!response.ok) {
		const body = await response.json().catch(() => null);
		const detail = typeof body?.detail === 'string' ? body.detail : response.statusText;
		throw new Error(`${response.status}: ${detail}`);
	}
	// 204 No Content has no body to parse
	return (response.status === 204 ? undefined : await response.json()) as T;
}

export const listTodos = () => request<Todo[]>('/todos');

export const createTodo = (data: TodoCreate) =>
	request<Todo>('/todos', { method: 'POST', body: JSON.stringify(data) });

export const updateTodo = (id: string, data: TodoUpdate) =>
	request<Todo>(`/todos/${id}`, { method: 'PUT', body: JSON.stringify(data) });

export const deleteTodo = (id: string) => request<void>(`/todos/${id}`, { method: 'DELETE' });
