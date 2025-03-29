import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-root',
  imports: [],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  message: string = 'Hello';

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.apiService.testConnection().subscribe((response: any) => {
      this.message = response.message;
    });
  }
}
