import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { SocketIoService } from './socket-io.service';
import { AuthService } from './auth.service';
import { filter, switchMap } from 'rxjs/operators';

interface UserNotification {
  user_id: string;
  doc_id: string;
  filename: string;
  status: 'COMPLETED' | 'FAILED';
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {

  constructor(
    private socketService: SocketIoService,
    private authService: AuthService,
    private snackBar: MatSnackBar,
    private router: Router
  ) {}

  initialize(): void {
    this.authService.currentUserId$.pipe(
      filter(userId => !!userId), // Only proceed if we have a user ID
      switchMap(userId => 
        this.socketService.listen<UserNotification>('user_notification').pipe(
          filter(notification => notification.user_id === userId)
        )
      )
    ).subscribe(notification => {
      this.showNotification(notification);
    });
  }

  private showNotification(notification: UserNotification): void {
    const message = `Document '${notification.filename}' has finished processing.`;
    const action = 'View';
    const snackBarRef = this.snackBar.open(message, action, {
      duration: 10000, // 10 seconds
      horizontalPosition: 'right',
      verticalPosition: 'top',
      panelClass: notification.status === 'FAILED' ? 'error-snackbar' : 'success-snackbar'
    });

    snackBarRef.onAction().subscribe(() => {
      this.router.navigate(['/documents', notification.doc_id]);
    });
  }
}