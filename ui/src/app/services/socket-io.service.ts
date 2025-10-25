import { Injectable } from '@angular/core';
import { io, Socket } from 'socket.io-client';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SocketIOService {
  private socket!: Socket;

  constructor() { }

  connect(): void {
    this.socket = io(environment.socketIoUrl);
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
    }
  }

  getSid(): string | undefined {
    return this.socket ? this.socket.id : undefined;
  }

  on(eventName: string): Observable<any> {
    return new Observable(observer => {
      this.socket.on(eventName, data => {
        observer.next(data);
      });
    });
  }
}
