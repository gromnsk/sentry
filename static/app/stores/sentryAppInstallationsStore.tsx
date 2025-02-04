import {createStore, StoreDefinition} from 'reflux';

import {SentryAppInstallation} from 'sentry/types';

interface SentryAppInstallationStoreDefinition extends StoreDefinition {
  getInitialState(): SentryAppInstallation[];
  load(items: SentryAppInstallation[]): void;
}

const storeConfig: SentryAppInstallationStoreDefinition = {
  init() {
    this.items = [];
  },

  getInitialState(): SentryAppInstallation[] {
    return this.items;
  },

  load(items: SentryAppInstallation[]) {
    this.items = items;
    this.trigger(items);
  },

  get(uuid: string) {
    const items: SentryAppInstallation[] = this.items;
    return items.find(item => item.uuid === uuid);
  },

  getAll(): SentryAppInstallation[] {
    return this.items;
  },
};

const SentryAppInstallationStore = createStore(storeConfig);
export default SentryAppInstallationStore;
