/*
 * The queue of submissions the app could not send.
 *
 * Only the page writes to it: it is the side that has the form, knows which submission the visitor
 * meant, and can say so on screen. The service worker reads it back and replays it, because that
 * has to keep working after the tab is gone.
 *
 * The two runtimes cannot share this file - the worker is rendered by Django and cannot import a
 * webpack bundle - so serviceworker.js carries its own copy of the three constants below. Change
 * one, change the other.
 */
export const OUTBOX_DATABASE = 'yamsa-outbox';
export const OUTBOX_STORE = 'entries';
export const OUTBOX_VERSION = 1;
export const OUTBOX_SYNC_TAG = 'yamsa-outbox';

const openOutbox = () =>
  new Promise((resolve, reject) => {
    const request = indexedDB.open(OUTBOX_DATABASE, OUTBOX_VERSION);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(OUTBOX_STORE)) {
        database.createObjectStore(OUTBOX_STORE, {keyPath: 'id'});
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });

const runTransaction = async (mode, work) => {
  const database = await openOutbox();
  try {
    return await new Promise((resolve, reject) => {
      const transaction = database.transaction(OUTBOX_STORE, mode);
      const result = work(transaction.objectStore(OUTBOX_STORE));
      transaction.oncomplete = () => resolve(result.value);
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(transaction.error);
    });
  } finally {
    database.close();
  }
};

export const readEntries = () =>
  runTransaction('readonly', (store) => {
    const request = store.getAll();
    const result = {};
    request.onsuccess = () => {
      result.value = request.result || [];
    };
    return result;
  });

export const putEntry = (entry) =>
  runTransaction('readwrite', (store) => {
    store.put(entry);
    return {value: entry};
  });

/*
 * A form as the queue has to hold it.
 *
 * Entries are kept as name/value pairs rather than as a FormData or a serialised string: files are
 * structured-cloneable and survive in IndexedDB as they are, which is what lets a receipt attached
 * offline reach the server with the expense it belongs to.
 */
export const serializeForm = (form) => Array.from(new FormData(form).entries());

export const CLIENT_REQUEST_ID_FIELD = 'client_request_id';

/*
 * Give the queued submission its own name, overwriting the one the form was rendered with.
 *
 * The form is served from the offline cache, so every expense entered without a connection starts
 * from the same copy and carries the same rendered id. Left alone, the second expense of a trip
 * would look to the server like a replay of the first and be dropped.
 */
const nameTheSubmission = (body, id) =>
  body
    .filter(([name]) => name !== CLIENT_REQUEST_ID_FIELD)
    .concat([[CLIENT_REQUEST_ID_FIELD, id]]);

export const buildEntry = ({form, url, roomSlug, scope, summary}) => {
  const id = crypto.randomUUID();

  return {
    id,
    url,
    roomSlug,
    // The account that queued this. Cache and queue outlive a session, and replaying an entry
    // under whoever is signed in now would book one person's expense against another.
    scope,
    summary,
    body: nameTheSubmission(serializeForm(form), id),
    createdAt: new Date().toISOString(),
    status: 'queued',
    attempts: 0,
    lastError: '',
  };
};
