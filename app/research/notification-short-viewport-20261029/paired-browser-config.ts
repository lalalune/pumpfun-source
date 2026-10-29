import { defineConfig } from '@playwright/test';
import { acceptedClickwrapState } from './tests/browser-state';
export default defineConfig({testDir:'./tests',testMatch:'notification-short-viewport.spec.ts',outputDir:'../../../work/notification-short-viewport/corrected-before/artifacts',retries:0,workers:1,timeout:30000,reporter:[['line'],['json',{outputFile:'../../../work/notification-short-viewport/corrected-before/report.json'}]],use:{baseURL:'http://127.0.0.1:3027',browserName:'chromium',storageState:acceptedClickwrapState,screenshot:'only-on-failure',trace:'retain-on-failure'}});
