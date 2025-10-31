import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, of } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { ProfileService, UserProfile } from './profile.service';
import { ThemeService } from './theme.service';

export interface AuthResponse {
  meta: { code: number };
  response?: {
    user: { id: string; email: string; };
    token: string;
  };
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
  ) {}

  checkAuthStatus(): Observable<boolean> {
    const token = this.getToken();
    if (!token) {
      this.clearUserState();
      return of(false);
    }

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
        if (response.response?.token) {
          this.storeToken(response.response.token);
          const user = response.response.user;
          this.updateUserState(user.id, user.email, []); // We don't have roles here
        }
      })
    );
  }

  loginWithMfa(email: string, totp_code: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login/mfa`, { email, totp_code }).pipe(
      tap((response) => {
        if (response.response?.token) {
          this.storeToken(response.response.token);
          const user = response.response.user;
          this.updateUserState(user.id, user.email, []); // We don't have roles here
        }
      })
    );
  }

  logout(): void {
    this.http.post(`${this.apiUrl}/logout`, {}).subscribe(() => {
      this.clearUserState();
      this.removeToken();
      this.router.navigate(['/login']);
    });
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  private storeToken(token: string): void {
    localStorage.setItem('auth_token', token);
  }

  private removeToken(): void {
    localStorage.removeItem('auth_token');
  }

  private initializeUserSession(): void {
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
