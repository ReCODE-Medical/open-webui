<script lang="ts">
	/**
	 * This is the main layout component for the application.
	 * It handles initialization, global state management, and keyboard shortcuts.
	 */
	
	// Import necessary dependencies
	import { toast } from 'svelte-sonner'; 				// Toast notifications
	import { onMount, tick, getContext } from 'svelte';	// Lifecycle hooks
	import { openDB, deleteDB, type IDBPDatabase } from 'idb';				// IndexedDB, used for storing large amounts of structured data on the client-side (in the user's browser)
	import fileSaver from 'file-saver';					// FileSaver, used to save chat logs
	import mermaid from 'mermaid';						// Mermaid, used to render flowcharts

	const { saveAs } = fileSaver;

	import { goto } from '$app/navigation';

	// Import API functions
	import { getModels as _getModels, getVersionUpdates } from '$lib/apis';
	import { getAllChatTags } from '$lib/apis/chats';
	import { getPrompts } from '$lib/apis/prompts';
	import { getDocs } from '$lib/apis/documents';
	import { getTools } from '$lib/apis/tools';

	import { getBanners } from '$lib/apis/configs';
	import { getUserSettings } from '$lib/apis/users';

	// Import stores. Stores are used to manage global state.
	import {
		user,
		showSettings,
		settings,
		models,
		prompts,
		documents,
		tags,
		banners,
		showChangelog,
		config,
		showCallOverlay,
		tools,
		functions,
		temporaryChatEnabled
	} from '$lib/stores';

	// Import components. Components are reusable pieces of UI.
	import SettingsModal from '$lib/components/chat/SettingsModal.svelte';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import ChangelogModal from '$lib/components/ChangelogModal.svelte';
	import AccountPending from '$lib/components/layout/Overlay/AccountPending.svelte';
	import { getFunctions } from '$lib/apis/functions';
	import { page } from '$app/stores';
	import { WEBUI_VERSION } from '$lib/constants';
	import { compareVersion } from '$lib/utils';

	import UpdateInfoToast from '$lib/components/layout/UpdateInfoToast.svelte';
	import { fade } from 'svelte/transition';

	// Get the i18n context
	const i18n = getContext('i18n');

	// Initialize variables
	let loaded = false;								// Flag to check if the app has loaded
	let DB: IDBPDatabase<unknown> | null = null;	// IndexedDB instance. Used to store chat logs
	let localDBChats: string | any[] = [];			// Local chat logs
	let version: { latest: any; current: any; };	// Version information

	/**
	 * Get models from the API.
	 */
	const getModels = async () => {
		return _getModels(localStorage.token);
	};

	// Lifecycle hook that runs when the component is mounted.
	onMount(async () => {
		
		// Check if the user is logged in.
		if ($user === undefined) {
			await goto('/auth');
		} else if (['user', 'admin'].includes($user.role)) {
			try {
				
				// Open the local IndexedDB database.
				DB = await openDB('Chats', 1);

				if (DB) {
					// Fetch and sort chats.
					const chats = await DB.getAllFromIndex('chats', 'timestamp');
					localDBChats = chats.map((item, idx) => chats[chats.length - 1 - idx]); // Reverse the order of chats so latest show first.

					// If there are no chats, delete the database.
					if (localDBChats.length === 0) {
						await deleteDB('Chats');
					}
				}

				console.log(DB);
			} catch (error) {
				// IndexedDB Not Found
			}

			// Get the user settings.
			const userSettings = await getUserSettings(localStorage.token).catch((error) => {
				console.error(error);
				return null;
			});

			if (userSettings) {
				settings.set(userSettings.ui);	// Set the user settings.
			} else {
				// If the user settings are not found, try to get them from localStorage.
				let localStorageSettings = {} as Parameters<(typeof settings)['set']>[0];

				try {
					localStorageSettings = JSON.parse(localStorage.getItem('settings') ?? '{}');
				} catch (e: unknown) {
					console.error('Failed to parse settings from localStorage', e);
				}
				settings.set(localStorageSettings);
			}

			// Fetch data in parallel from the API.
			await Promise.all([
				(async () => {
					models.set(await getModels());
				})(),
				(async () => {
					prompts.set(await getPrompts(localStorage.token));
				})(),
				(async () => {
					documents.set(await getDocs(localStorage.token));
				})(),
				(async () => {
					tools.set(await getTools(localStorage.token));
				})(),
				(async () => {
					functions.set(await getFunctions(localStorage.token));
				})(),
				(async () => {
					banners.set(await getBanners(localStorage.token));
				})(),
				(async () => {
					tags.set(await getAllChatTags(localStorage.token));
				})()
			]);

			// Setup global keyboard shortcuts
			document.addEventListener('keydown', function (event) {
				const isCtrlPressed = event.ctrlKey || event.metaKey; // metaKey is for Cmd key on Mac
				// Check if the Shift key is pressed
				const isShiftPressed = event.shiftKey;

				// Check if Ctrl + Shift + O is pressed
				if (isCtrlPressed && isShiftPressed && event.key.toLowerCase() === 'o') {
					event.preventDefault();
					console.log('newChat');
					document.getElementById('sidebar-new-chat-button')?.click();
				}

				// Check if Shift + Esc is pressed
				if (isShiftPressed && event.key === 'Escape') {
					event.preventDefault();
					console.log('focusInput');
					document.getElementById('chat-textarea')?.focus();
				}

				// Check if Ctrl + Shift + ; is pressed
				if (isCtrlPressed && isShiftPressed && event.key === ';') {
					event.preventDefault();
					console.log('copyLastCodeBlock');
					const button = [...document.getElementsByClassName('copy-code-button')]?.at(-1);
					button?.click();
				}

				// Check if Ctrl + Shift + C is pressed
				if (isCtrlPressed && isShiftPressed && event.key.toLowerCase() === 'c') {
					event.preventDefault();
					console.log('copyLastResponse');
					const button = [...document.getElementsByClassName('copy-response-button')]?.at(-1);
					console.log(button);
					button?.click();
				}

				// Check if Ctrl + Shift + S is pressed
				if (isCtrlPressed && isShiftPressed && event.key.toLowerCase() === 's') {
					event.preventDefault();
					console.log('toggleSidebar');
					document.getElementById('sidebar-toggle-button')?.click();
				}

				// Check if Ctrl + Shift + Backspace is pressed
				if (isCtrlPressed && isShiftPressed && event.key === 'Backspace') {
					event.preventDefault();
					console.log('deleteChat');
					document.getElementById('delete-chat-button')?.click();
				}

				// Check if Ctrl + . is pressed
				if (isCtrlPressed && event.key === '.') {
					event.preventDefault();
					console.log('openSettings');
					showSettings.set(!$showSettings);
				}

				// Check if Ctrl + / is pressed
				if (isCtrlPressed && event.key === '/') {
					event.preventDefault();
					console.log('showShortcuts');
					document.getElementById('show-shortcuts-button')?.click();
				}
			});

			// Show the changelog if the version has changed for the admin user.
			if ($user.role === 'admin') {
				// Since config could be null, we set set a default value of 'version' to prevent errors.
				showChangelog.set(localStorage.version !== ($config?.version ?? ''));
			}

			// Enable temporary chat if specified in URL
			if ($page.url.searchParams.get('temporary-chat') === 'true') {
				temporaryChatEnabled.set(true);
			}

			// Check for version updates for admin users
			if ($user.role === 'admin') {
				// Check if the user has dismissed the update toast in the last 24 hours
				if (localStorage.dismissedUpdateToast) {
					const dismissedUpdateToast = new Date(Number(localStorage.dismissedUpdateToast));
					const now = new Date();

					if (now.getTime() - dismissedUpdateToast.getTime() > 24 * 60 * 60 * 1000) {
						await checkForVersionUpdates();
					}
				} else {
					await checkForVersionUpdates();
				}
			}
			await tick();
		}

		loaded = true;
	});

	/**
	 * Check for version updates.
	 */
	const checkForVersionUpdates = async () => {
		version = await getVersionUpdates().catch((error) => {
			return {
				current: WEBUI_VERSION,
				latest: WEBUI_VERSION
			};
		});
	};
</script>

<!-- The following code is the main layout of the application. -->
<SettingsModal bind:show={$showSettings} />
<ChangelogModal bind:show={$showChangelog} />

<!-- Show update toast if a newer version is available -->
{#if version && compareVersion(version.latest, version.current)}
	<div class=" absolute bottom-8 right-8 z-50" in:fade={{ duration: 100 }}>
		<UpdateInfoToast {version} />
	</div>
{/if}

<div class="app relative">
	<div
		class=" text-gray-700 dark:text-gray-100 bg-white dark:bg-gray-900 h-screen max-h-[100dvh] overflow-auto flex flex-row"
	>
		{#if loaded}
			{#if !['user', 'admin'].includes($user?.role ?? '')}
				<AccountPending />
			{:else if localDBChats.length > 0}
				
			<!-- Show migration dialog for old IndexedDB chats. -->
				<div class="fixed w-full h-full flex z-50">
					<div
						class="absolute w-full h-full backdrop-blur-md bg-white/20 dark:bg-gray-900/50 flex justify-center"
					>
						<div class="m-auto pb-44 flex flex-col justify-center">
							<div class="max-w-md">
								<div class="text-center dark:text-white text-2xl font-medium z-50">
									Important Update<br /> Action Required for Chat Log Storage
								</div>

								<div class=" mt-4 text-center text-sm dark:text-gray-200 w-full">
									
									<!-- Migration instructions. -->
									{$i18n.t(
										"Saving chat logs directly to your browser's storage is no longer supported. Please take a moment to download and delete your chat logs by clicking the button below. Don't worry, you can easily re-import your chat logs to the backend through"
									)}
									<span class="font-semibold dark:text-white"
										>{$i18n.t('Settings')} > {$i18n.t('Chats')} > {$i18n.t('Import Chats')}</span
									>. {$i18n.t(
										'This ensures that your valuable conversations are securely saved to your backend database. Thank you!'
									)}
								</div>

								<div class=" mt-6 mx-auto relative group w-fit">
									<button
										class="relative z-20 flex px-5 py-2 rounded-full bg-white border border-gray-100 dark:border-none hover:bg-gray-100 transition font-medium text-sm"
										on:click={async () => {
											let blob = new Blob([JSON.stringify(localDBChats)], {
												type: 'application/json'
											});
											saveAs(blob, `chat-export-${Date.now()}.json`);

											const tx = DB.transaction('chats', 'readwrite');
											await Promise.all([tx.store.clear(), tx.done]);
											await deleteDB('Chats');

											localDBChats = [];
										}}
									>
										Download & Delete
									</button>

									<button
										class="text-xs text-center w-full mt-2 text-gray-400 underline"
										on:click={async () => {
											localDBChats = [];
										}}>{$i18n.t('Close')}</button
									>
								</div>
							</div>
						</div>
					</div>
				</div>
			{/if}

			<Sidebar />
			<slot />
		{/if}
	</div>
</div>

<style>
	.loading {
		display: inline-block;
		clip-path: inset(0 1ch 0 0);
		animation: l 1s steps(3) infinite;
		letter-spacing: -0.5px;
	}

	@keyframes l {
		to {
			clip-path: inset(0 -1ch 0 0);
		}
	}

	pre[class*='language-'] {
		position: relative;
		overflow: auto;

		/* make space  */
		margin: 5px 0;
		padding: 1.75rem 0 1.75rem 1rem;
		border-radius: 10px;
	}

	pre[class*='language-'] button {
		position: absolute;
		top: 5px;
		right: 5px;

		font-size: 0.9rem;
		padding: 0.15rem;
		background-color: #828282;

		border: ridge 1px #7b7b7c;
		border-radius: 5px;
		text-shadow: #c4c4c4 0 0 2px;
	}

	pre[class*='language-'] button:hover {
		cursor: pointer;
		background-color: #bcbabb;
	}
</style>
