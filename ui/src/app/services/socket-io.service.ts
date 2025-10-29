import { Injectable } from '@angular/core';
import { io, Socket } from 'socket.io-client';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SocketIoService {
  private socket: Socket;

  constructor() {
    this.socket = io(environment.socketUrl, {
      transports: ['websocket']
    });
  }

  listen<T>(eventName: string): Observable<T> {
    return new Observable(observer => {
      this.socket.on(eventName, (data: T) => {
        observer.next(data);
      });

      // Teardown logic
      return () => this.socket.off(eventName);
    });
  }

  emit(eventName: string, data: any) {
    this.socket.emit(eventName, data);
  }
}
