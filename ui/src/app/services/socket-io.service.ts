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
      autoConnect: false, // We will connect manually
      transports: ['websocket']
    });
  }

  connect() {
    this.socket.connect();
  }

  disconnect() {
    this.socket.disconnect();
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

  getSid(): string | undefined {
    return this.socket.id;
  }
  
  // Adding the 'on' method back for compatibility
  on(eventName: string): Observable<any> {
    return this.listen(eventName);
  }
}
