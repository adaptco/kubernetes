use sha2::{Digest, Sha256};
use std::collections::HashMap;

/// Result type for Stage-5 Refusal checks.
/// If Ok, the system proceeds. If Err, the system HALTS immediately (Stage-5 Refusal).
pub type RefusalResult<T> = Result<T, RefusalError>;

#[derive(Debug, Clone)]
pub enum RefusalError {
    ProvenanceMismatch { expected: String, actual: String },
    ConfigDrift { parameter: String, expected: String, actual: String },
    UnauthorizedReplay { blob_id: String },
    IntegrityFailure(String),
}

/// A "Vaulted Blob" represents a fossilized, immutable save-state.
/// This matches the "Truth Capsules" in the spec.
#[derive(Debug, Clone)]
pub struct VaultedBlob {
    pub id: String,
    pub timestamp: u64,
    /// Raw state vector from the emulator (NES-class environment)
    pub state_vector: Vec<u8>,
    pub metadata: HashMap<String, String>,
    pub signature: String, 
}

/// The Kaiser-EKF Integrity Sentinel.
/// Acts as the gatekeeper for the emulator state.
pub struct IntegritySentinel {
    /// Trusted registry of known-good blob hashes (The "Ledger").
    known_hashes: HashMap<String, String>,
    /// Authorized configuration parameters to prevent drift.
    config_manifest: HashMap<String, String>,
}

impl IntegritySentinel {
    pub fn new(known_hashes: HashMap<String, String>, config_manifest: HashMap<String, String>) -> Self {
        Self {
            known_hashes,
            config_manifest,
        }
    }

    /// Primary Gate: Verifies the provenance of a vaulted blob before ingestion.
    /// This ensures we only load from the "Truth Capsules".
    pub fn verify_provenance(&self, blob: &VaultedBlob) -> RefusalResult<()> {
        // 1. Calculate Hash of the State Vector
        let mut hasher = Sha256::new();
        hasher.update(&blob.state_vector);
        // Using hex encoding for string comparison
        let hash_result = hex::encode(hasher.finalize());

        // 2. Check against the Trusted Registry
        if let Some(trusted_hash) = self.known_hashes.get(&blob.id) {
            if hash_result != *trusted_hash {
                return Err(RefusalError::ProvenanceMismatch {
                    expected: trusted_hash.clone(),
                    actual: hash_result,
                });
            }
        } else {
            return Err(RefusalError::UnauthorizedReplay {
                blob_id: blob.id.clone(),
            });
        }

        // 3. Verify Metadata Signature
        self.verify_signature(blob)?;

        Ok(())
    }

    /// Secondary Gate: Monitors for Config Drift during runtime.
    /// Ensures the emulator environment matches the verified spec.
    pub fn check_drift(&self, current_config: &HashMap<String, String>) -> RefusalResult<()> {
        for (key, trusted_value) in &self.config_manifest {
            if let Some(current_value) = current_config.get(key) {
                if current_value != trusted_value {
                    return Err(RefusalError::ConfigDrift {
                        parameter: key.clone(),
                        expected: trusted_value.clone(),
                        actual: current_value.clone(),
                    });
                }
            } else {
                // Critical config missing
                return Err(RefusalError::ConfigDrift {
                    parameter: key.clone(),
                    expected: trusted_value.clone(),
                    actual: "MISSING".to_string(),
                });
            }
        }
        Ok(())
    }

    fn verify_signature(&self, blob: &VaultedBlob) -> RefusalResult<()> {
        if blob.signature.is_empty() {
            return Err(RefusalError::IntegrityFailure("Missing or invalid blob signature".into()));
        }
        // In a real implementation, we would verify the cryptographic signature here.
        Ok(())
    }
}

/// The Stage-5 Refusal Harness.
/// This module integrates the checkpoints into the loading lifecycle.
pub mod check_harness {
    use super::*;

    /// Threads the needle: Only proceeds if both Provenance and Config are green.
    pub fn execute_load_sequence(
        sentinel: &IntegritySentinel, 
        blob: &VaultedBlob, 
        runtime_config: &HashMap<String, String>
    ) -> RefusalResult<()> {
        println!("[Stage-5] Initiating Load Sequence for Blob: {}", blob.id);
        
        // Step 1: Provenance (The "Technical Truth" check)
        match sentinel.verify_provenance(blob) {
            Ok(_) => println!("[Stage-5] Provenance Verified. Hash matches Truth Capsule."),
            Err(e) => {
                eprintln!("[Stage-5] REFUSAL: Provenance mismatch. The blob is tainted. HALTING.");
                return Err(e);
            }
        }

        // Step 2: Drift Check (The "No Hallucination" check)
        match sentinel.check_drift(runtime_config) {
            Ok(_) => println!("[Stage-5] Config Integrity Verified. Zero Drift detected."),
            Err(e) => {
                eprintln!("[Stage-5] REFUSAL: Config drift detected. Environment unsafe. HALTING.");
                return Err(e);
            }
        }

        println!("[Stage-5] GREEN LIGHT. Handing off state to Emulator Core.");
        Ok(())
    }
}
