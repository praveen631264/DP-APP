import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './services/auth.service';
import { map, catchError, of } from 'rxjs';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.checkAuthStatus().pipe(
    map(isLoggedIn => {
      if (isLoggedIn) {
        return true;
      }
      return router.createUrlTree(['/login']);
    }),
    catchError(() => of(router.createUrlTree(['/login'])))
  );
};

export const adminGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // This guard relies on an AuthService that can fetch the current user
  // and check their roles.
  return authService.getCurrentUser().pipe(
    map(user => {
      if (user && user.roles.includes('Admin')) {
        return true; // Allow access
      }
      return router.createUrlTree(['/dashboard']); // Redirect non-admins
    }),
    catchError(() => of(router.createUrlTree(['/login']))) // On error, redirect to login
  );
};