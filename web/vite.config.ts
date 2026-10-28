import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// Where the dev server forwards /api requests. In Docker this is http://api:8000.
const apiUrl = process.env.API_URL ?? 'http://localhost:8000';

export default defineConfig({
	plugins: [
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},
			// SPA: every URL that is not a prerendered file is served by 200.html.
			adapter: adapter({ fallback: '200.html' })
		})
	],
	server: {
		host: true, // listen on 0.0.0.0 so the container port is reachable
		port: 5173,
		strictPort: true,
		proxy: {
			// The browser always calls /api/..., so no CORS is needed on the API.
			'/api': {
				target: apiUrl,
				changeOrigin: true,
				rewrite: (path) => path.replace(/^\/api/, '')
			}
		}
	}
});
