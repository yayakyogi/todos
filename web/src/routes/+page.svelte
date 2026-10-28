<script lang="ts">
	import { createTodo, deleteTodo, listTodos, updateTodo, type Todo } from '#lib/api.ts';

	let todos = $state<Todo[]>([]);
	let title = $state('');
	let loading = $state(true);
	let error = $state<string | null>(null);

	let remaining = $derived(todos.filter((todo) => todo.status === 'open').length);

	// Run an API call and show its error message instead of failing silently.
	async function run(action: () => Promise<void>) {
		error = null;
		try {
			await action();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function load() {
		await run(async () => {
			todos = await listTodos();
		});
		loading = false;
	}

	async function add(event: SubmitEvent) {
		event.preventDefault();
		const value = title.trim();
		if (!value) return;
		await run(async () => {
			todos.push(await createTodo({ title: value }));
			title = '';
		});
	}

	async function toggle(todo: Todo) {
		const status = todo.status === 'open' ? 'completed' : 'open';
		await run(async () => {
			const updated = await updateTodo(todo.id, { status });
			todos = todos.map((t) => (t.id === updated.id ? updated : t));
		});
	}

	async function remove(todo: Todo) {
		await run(async () => {
			await deleteTodo(todo.id);
			todos = todos.filter((t) => t.id !== todo.id);
		});
	}

	load();
</script>

<svelte:head>
	<title>Todos</title>
</svelte:head>

<main>
	<h1>Todos</h1>

	<form onsubmit={add}>
		<input bind:value={title} placeholder="What needs to be done?" maxlength="255" />
		<button type="submit" disabled={!title.trim()}>Add</button>
	</form>

	{#if error}
		<p class="error" role="alert">{error}</p>
	{/if}

	{#if loading}
		<p class="muted">Loading…</p>
	{:else if todos.length === 0}
		<p class="muted">No todos yet.</p>
	{:else}
		<ul>
			{#each todos as todo (todo.id)}
				<li class:done={todo.status === 'completed'}>
					<label>
						<input
							type="checkbox"
							checked={todo.status === 'completed'}
							onchange={() => toggle(todo)}
						/>
						<span>{todo.title}</span>
					</label>
					<button class="delete" onclick={() => remove(todo)} aria-label="Delete {todo.title}">
						✕
					</button>
				</li>
			{/each}
		</ul>
		<p class="muted">{remaining} of {todos.length} remaining</p>
	{/if}
</main>

<style>
	main {
		max-width: 32rem;
		margin: 3rem auto;
		padding: 0 1rem;
		font-family: system-ui, sans-serif;
	}

	form {
		display: flex;
		gap: 0.5rem;
	}

	form input {
		flex: 1;
		padding: 0.5rem;
	}

	ul {
		list-style: none;
		padding: 0;
	}

	li {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.5rem 0;
		border-bottom: 1px solid #ddd;
	}

	li.done span {
		text-decoration: line-through;
		opacity: 0.6;
	}

	label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.delete {
		border: none;
		background: none;
		cursor: pointer;
		opacity: 0.6;
	}

	.error {
		color: #c00;
	}

	.muted {
		color: #666;
	}
</style>
