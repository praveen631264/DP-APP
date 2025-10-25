import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, of } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { ProfileService, UserProfile } from './profile.service';
import { ThemeService } from './theme.service';

export interface AuthResponse {
  message: string;
  mfa_required?: boolean;
}

export interface UserStatus {
  id: string;
  email: string;
  roles: string[];
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = '/api/v1/auth';
  private _isLoggedIn$ = new BehaviorSubject<boolean>(false);
  private _currentUserEmail$ = new BehaviorSubject<string | null>(null);
  private _currentUserId$ = new BehaviorSubject<string | null>(null);
  private _currentUserRoles$ = new BehaviorSubject<string[]>([]);
  isLoggedIn$ = this._isLoggedIn$.asObservable();
  currentUserEmail$ = this._currentUserEmail$.asObservable();
  currentUserId$ = this._currentUserId$.asObservable();
  currentUserRoles$ = this._currentUserRoles$.asObservable();

  constructor(
    private http: HttpClient, 
    private router: Router,
    private profileService: ProfileService,
    private themeService: ThemeService
  ) {
    this.checkAuthenticationStatus().subscribe();
  }

  checkAuthenticationStatus(): Observable<boolean> {
    return this.http.get<UserStatus>(`${this.apiUrl}/status`).pipe(
      map(user => {
        this.updateUserState(user.id, user.email, user.roles);
        this.initializeUserSession();
        return true;
      }),
      catchError(() => {
        this.clearUserState();
        return of(false);
      })
    );
  }

  login(credentials: { email: string, password: string }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, credentials).pipe(
      tap(response => {
        if (!response.mfa_required) {
          this.checkAuthenticationStatus().subscribe();
        }
      })
    );
  }

  loginWithMfa(email: string, totp_code: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login/mfa`, { email, totp_code }).pipe(
      tap(() => {
        this.checkAuthenticationStatus().subscribe();
      })
    );
  }

  logout(): void {
    this.http.post(`${this.apiUrl}/logout`, {}).subscribe(() => {
      this.clearUserState();
      this.router.navigate(['/login']);
    });
  }

  private initializeUserSession(): void {
    // On initial load, also fetch profile to set the theme
    this.profileService.getProfile().subscribe((profile: UserProfile) => {
      if (profile?.preferences?.theme) {
        this.themeService.setTheme(profile.preferences['theme'] || 'default-light');
      }
    });
  }

  private updateUserState(id: string, email: string, roles: string[]): void {
    this._isLoggedIn$.next(true);
    this._currentUserId$.next(id);
    this._currentUserEmail$.next(email);
    this._currentUserRoles$.next(roles);
  }

  private clearUserState(): void {
    this._isLoggedIn$.next(false);
    this._currentUserId$.next(null);
    this._currentUserEmail$.next(null);
    this._currentUserRoles$.next([]);
  }

  hasRole(role: string): Observable<boolean> {
    return this.currentUserRoles$.pipe(map(roles => roles.includes(role)));
  }

  getCurrentUser(): Observable<UserProfile | null> {
    if (!this._isLoggedIn$.value) {
      return of(null);
    }
    return this.profileService.getProfile();
  }
}