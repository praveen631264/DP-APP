import { Injectable } from '@angular/core';
import { io, Socket } from 'socket.io-client';
import { Observable, Subscriber } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SocketIoService {
  private socket: Socket;

  constructor() {
    // In production, you might need to specify the URL
    this.socket = io();
  }

  // Listen for a specific event
  listen<T>(eventName: string): Observable<T> {
    return new Observable((subscriber: Subscriber<T>) => {
      this.socket.on(eventName, (data: T) => {
        subscriber.next(data);
      });
    });
  }

  // Get the unique session ID for this client
  getSessionId(): string {
    return this.socket.id;
  }
}