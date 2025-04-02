import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { RouterOutlet } from '@angular/router';
import { ApiService } from '../api.service';
import { finalize } from 'rxjs/operators';

// --- Import Angular Material Modules ---
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatListModule } from '@angular/material/list';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon'; // Optional: for icons

// --- Ensure Animations are provided (if you chose 'Yes' during ng add) ---
// Usually ng add handles this in app.config.ts by adding provideAnimations()
// or imports BrowserAnimationsModule/NoopAnimationsModule in app.module.ts

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    HttpClientModule,
    // --- Add Material Modules here ---
    MatButtonModule,
    MatCardModule,
    MatProgressSpinnerModule,
    MatListModule,
    MatDividerModule,
    MatIconModule, // Optional
     // BrowserAnimationsModule // <-- Add if using AppModule and not standalone with provideAnimations()
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  // --- Component Properties ---
  selectedFile: File | null = null;
  uploadMessage: string = '';
  analysisMessage: string = '';
  uploadedPdfId: number | null = null;
  analysisResults: string[] = [];
  isLoading: boolean = false;

  constructor(private apiService: ApiService) {}

  // --- Event Handlers ---
  // (Methods: onFileSelected, onUpload, onAnalyze, onFetchResults remain the same as before)
   onFileSelected(event: any): void {
    const fileInput = event.target as HTMLInputElement;
    if (fileInput.files && fileInput.files.length > 0) {
      this.selectedFile = fileInput.files[0];
      this.uploadMessage = '';
      this.analysisMessage = '';
      this.uploadedPdfId = null;
      this.analysisResults = [];
    } else {
      this.selectedFile = null;
    }
  }

  onUpload(): void {
    if (!this.selectedFile) {
      this.uploadMessage = 'Please select a PDF file first.';
      return;
    }
    this.isLoading = true;
    this.uploadMessage = '';
    this.analysisMessage = '';
    this.analysisResults = [];
    this.uploadedPdfId = null;
    const formData = new FormData();
    formData.append('file', this.selectedFile, this.selectedFile.name);
    this.apiService.uploadPdf(formData)
      .pipe(finalize(() => this.isLoading = false))
      .subscribe({
        next: (response: any) => {
          this.uploadMessage = response.message || 'Upload successful!';
          this.uploadedPdfId = response.pdf_id;
          console.log('Upload successful, PDF ID:', this.uploadedPdfId);
        },
        error: (error: Error) => {
          this.uploadMessage = `Upload failed: ${error.message}`;
          console.error('Upload error details:', error);
        }
      });
  }

  onAnalyze(): void {
    if (!this.uploadedPdfId) {
      this.analysisMessage = 'Please upload a PDF successfully first.';
      return;
    }
    this.isLoading = true;
    this.analysisMessage = 'Starting analysis...';
    this.analysisResults = [];
    this.apiService.analyzePdf(this.uploadedPdfId)
      // No finalize here, as fetchResults will set isLoading=false
      .subscribe({
        next: (response: any) => {
          this.analysisMessage = response.message || 'Analysis request sent successfully. Fetching results...';
          console.log('Analysis triggered:', response);
          this.onFetchResults(); // Automatically fetch results
        },
        error: (error: Error) => {
          this.analysisMessage = `Analysis request failed: ${error.message}`;
          console.error('Analysis trigger error details:', error);
          this.isLoading = false; // Set loading false on analyze error
        }
      });
  }

   onFetchResults(): void {
    if (!this.uploadedPdfId) {
      this.analysisMessage = 'Cannot fetch results. No PDF has been uploaded and analyzed successfully yet.';
       this.isLoading = false; // Ensure loading stops if called erroneously
      return;
    }
    // Ensure isLoading is true if called directly or after analysis starts
    this.isLoading = true;
    this.analysisMessage = 'Fetching analysis results...';
    this.analysisResults = [];
    this.apiService.getAnalysisResults(this.uploadedPdfId)
      .pipe(finalize(() => this.isLoading = false)) // Finalize applies here
      .subscribe({
        next: (response: any) => {
           if (response && response.components) {
             this.analysisResults = response.components;
             this.analysisMessage = `Found ${this.analysisResults.length} component(s).`;
             if (this.analysisResults.length === 0) {
                 this.analysisMessage += " (No components extracted or analysis did not yield results).";
             }
           } else {
              this.analysisResults = [];
              this.analysisMessage = 'Received results, but component data is missing.';
           }
           console.log('Analysis results received:', this.analysisResults);
        },
        error: (error: Error) => {
           this.analysisMessage = `Failed to fetch results: ${error.message}`;
           console.error('Fetch results error details:', error);
        }
      });
   }
}