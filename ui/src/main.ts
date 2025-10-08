import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { importProvidersFrom } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { App } from './app/app';

bootstrapApplication(App, {
  providers: [
    importProvidersFrom(FormsModule),
    provideHttpClient(withInterceptorsFromDi()),
  ]
});
