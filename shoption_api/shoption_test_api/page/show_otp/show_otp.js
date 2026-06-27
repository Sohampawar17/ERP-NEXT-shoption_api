frappe.pages['show-otp'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'OTP Management',
        single_column: true
    });

    // Create enhanced HTML elements
    let content = $(`
        <div style="max-width: 900px;">
            <!-- Input Section -->
            <div style="background: var(--color-background-primary); border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-lg); padding: 1.5rem; margin-bottom: 1.5rem;">
                <div style="display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 250px;">
                        <label style="display: block; font-size: 13px; color: var(--color-text-secondary); margin-bottom: 6px; font-weight: 500;">Mobile Number</label>
                        <input type="text" id="mobile_no" placeholder="Enter 10-digit mobile number" class="form-control" style="width: 100%; padding: 8px 12px; border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); font-size: 14px;">
                    </div>
                    <button class="btn btn-primary" id="show_otp_btn" style="padding: 8px 20px; font-size: 14px;">Show OTP</button>
                </div>
            </div>

            <!-- OTP Display Section -->
            <div id="otp_info_container" style="display: none;">
                <!-- OTP Code Card -->
                <div style="background: var(--color-background-secondary); border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-lg); padding: 1.5rem; margin-bottom: 1.5rem;">
                    <p style="font-size: 13px; color: var(--color-text-secondary); margin: 0 0 12px 0; font-weight: 500; text-transform: uppercase;">Generated OTP</p>
                    <div style="display: flex; align-items: center; gap: 16px;">
                        <div style="background: var(--color-background-info); border-radius: var(--border-radius-md); padding: 20px 30px; min-width: 180px;">
                            <p style="font-size: 12px; color: var(--color-text-info); margin: 0 0 8px 0; letter-spacing: 2px;">OTP CODE</p>
                            <p id="otp_code_display" style="font-size: 32px; font-weight: 500; margin: 0; color: var(--color-text-info); letter-spacing: 4px; font-family: var(--font-mono);">------</p>
                        </div>
                        <button id="copy_otp_btn" style="padding: 8px 16px; background: var(--color-background-primary); border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); cursor: pointer; font-size: 13px; color: var(--color-text-primary);">📋 Copy</button>
                    </div>
                </div>

                <!-- Customer Details Card -->
                <div style="background: var(--color-background-primary); border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-lg); padding: 1.5rem; margin-bottom: 1.5rem;">
                    <h3 style="font-size: 16px; font-weight: 500; margin: 0 0 16px 0; color: var(--color-text-primary);">Customer Information</h3>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                        <!-- Customer Name -->
                        <div style="background: var(--color-background-secondary); padding: 12px; border-radius: var(--border-radius-md);">
                            <p style="font-size: 12px; color: var(--color-text-secondary); margin: 0 0 6px 0; font-weight: 500;">CUSTOMER NAME</p>
                            <p id="customer_name_display" style="font-size: 15px; color: var(--color-text-primary); margin: 0; font-weight: 500;">-</p>
                        </div>

                        <!-- Mobile Number -->
                        <div style="background: var(--color-background-secondary); padding: 12px; border-radius: var(--border-radius-md);">
                            <p style="font-size: 12px; color: var(--color-text-secondary); margin: 0 0 6px 0; font-weight: 500;">MOBILE NUMBER</p>
                            <p id="mobile_display" style="font-size: 15px; color: var(--color-text-primary); margin: 0; font-weight: 500;">-</p>
                        </div>

                        <!-- Customer ID -->
                        <div style="background: var(--color-background-secondary); padding: 12px; border-radius: var(--border-radius-md);">
                            <p style="font-size: 12px; color: var(--color-text-secondary); margin: 0 0 6px 0; font-weight: 500;">CUSTOMER ID</p>
                            <p id="customer_id_display" style="font-size: 15px; color: var(--color-text-primary); margin: 0; font-weight: 500;">-</p>
                        </div>
                    </div>
                </div>

                <!-- OTP Status Card -->
                <div style="background: var(--color-background-primary); border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-lg); padding: 1.5rem; margin-bottom: 1.5rem;">
                    <h3 style="font-size: 16px; font-weight: 500; margin: 0 0 16px 0; color: var(--color-text-primary);">OTP Status</h3>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px;">
                        <!-- OTP Validity -->
                        <div style="background: var(--color-background-secondary); padding: 12px; border-radius: var(--border-radius-md);">
                            <p style="font-size: 12px; color: var(--color-text-secondary); margin: 0 0 6px 0; font-weight: 500;">VALIDITY</p>
                            <p id="otp_validity_display" style="font-size: 15px; color: var(--color-text-primary); margin: 0; font-weight: 500;">-</p>
                        </div>

                        <!-- Expiry Time -->
                        <div style="background: var(--color-background-secondary); padding: 12px; border-radius: var(--border-radius-md);">
                            <p style="font-size: 12px; color: var(--color-text-secondary); margin: 0 0 6px 0; font-weight: 500;">EXPIRES AT</p>
                            <p id="otp_expiry_display" style="font-size: 15px; color: var(--color-text-warning); margin: 0; font-weight: 500;">--:--:--</p>
                        </div>

                        <!-- Attempts Remaining -->
                        <div style="background: var(--color-background-secondary); padding: 12px; border-radius: var(--border-radius-md);">
                            <p style="font-size: 12px; color: var(--color-text-secondary); margin: 0 0 6px 0; font-weight: 500;">ATTEMPTS LEFT</p>
                            <p id="otp_attempts_display" style="font-size: 15px; color: var(--color-text-primary); margin: 0; font-weight: 500;">-/-</p>
                        </div>

                        <!-- Status Badge -->
                        <div style="background: var(--color-background-secondary); padding: 12px; border-radius: var(--border-radius-md);">
                            <p style="font-size: 12px; color: var(--color-text-secondary); margin: 0 0 6px 0; font-weight: 500;">STATUS</p>
                            <span id="otp_status_badge" style="display: inline-block; background: var(--color-background-success); color: var(--color-text-success); padding: 4px 12px; border-radius: var(--border-radius-md); font-size: 12px; font-weight: 500;">Active</span>
                        </div>
                    </div>

                    <!-- Timer Bar -->
                    <div style="margin-top: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <p style="font-size: 12px; color: var(--color-text-secondary); margin: 0; font-weight: 500;">COUNTDOWN</p>
                            <p id="timer_text" style="font-size: 12px; color: var(--color-text-primary); margin: 0; font-weight: 500;">00:00</p>
                        </div>
                        <div style="height: 6px; background: var(--color-background-secondary); border-radius: 3px; overflow: hidden;">
                            <div id="timer_bar" style="height: 100%; background: var(--color-background-warning); width: 0%; transition: width 1s linear; border-radius: 3px;"></div>
                        </div>
                    </div>
                </div>

                <!-- Actions -->
                <div style="display: flex; gap: 12px; margin-top: 1.5rem;">
                    <button id="clear_otp_btn" style="padding: 8px 16px; background: var(--color-background-primary); border: 0.5px solid var(--color-border-secondary); border-radius: var(--border-radius-md); cursor: pointer; font-size: 14px; color: var(--color-text-primary);">Clear</button>
                </div>
            </div>

            <!-- Message Area -->
            <div id="message_container" style="display: none; margin-top: 1rem;">
                <div id="alert_message" style="padding: 12px 16px; border-radius: var(--border-radius-md); font-size: 13px; border-left: 3px solid var(--color-border-success);"></div>
            </div>
        </div>
    `);

    $(page.body).append(content);

    // OTP Data Storage
    let otpData = {
        code: null,
        mobileNo: null,
        customerName: null,
        customerId: null,
        expiryTime: null,
        validity: 0,
        attempts: 0,
        maxAttempts: 0,
        timerInterval: null
    };

    // Button click event
    $("#show_otp_btn").click(function() {
        let mobile = $("#mobile_no").val().trim();
        if(!mobile) {
            showMessage("Please enter a mobile number", "error");
            return;
        }

        frappe.call({
            method: "shoption_api.shoption_test_api.page.show_otp.show_otp.get_last_otp", // replace with your API path
            args: { mobile_no: mobile },
            callback: function(r) {
                if(r.message && r.message.status) {
                    displayOTPInfo(r.message);
                } else {
                    showMessage(r.message.message || "Error fetching OTP", "error");
                }
            },
            error: function(err) {
                showMessage("Error fetching OTP details", "error");
                console.log(err);
            }
        });
    });

    function displayOTPInfo(data) {
        const now = new Date();
        let expiryTime = new Date(data.expiry || data.expiry_time);
        
        otpData = {
            code: data.otp,
            mobileNo: data.mobile_no || mobile,
            customerName: data.customer_name || '-',
            customerId: data.customer_id || '-',
            expiryTime: expiryTime,
            validity: Math.ceil((expiryTime - now) / 1000),
            attempts: data.attempts_remaining !== undefined ? data.attempts_remaining : (data.attempts || 0),
            maxAttempts: data.max_attempts || 3,
            timerInterval: null
        };
        
        // Update UI
        $("#otp_code_display").text(otpData.code);
        $("#customer_name_display").text(otpData.customerName);
        $("#mobile_display").text(formatMobileNumber(otpData.mobileNo));
        $("#customer_id_display").text(otpData.customerId);
        $("#otp_attempts_display").text(otpData.attempts + '/' + otpData.maxAttempts);
        
        // Calculate validity in minutes
        let validityMinutes = Math.ceil(otpData.validity / 60);
        $("#otp_validity_display").text(validityMinutes + " minutes");
        
        $("#otp_info_container").show();
        
        // Start countdown timer
        startTimer();
        
        // Show success message
        showMessage(`OTP details retrieved for ${formatMobileNumber(otpData.mobileNo)}`, "success");
    }

    function startTimer() {
        // Clear previous interval if exists
        if (otpData.timerInterval) {
            clearInterval(otpData.timerInterval);
        }
        
        otpData.timerInterval = setInterval(function() {
            const now = new Date();
            const timeLeft = (otpData.expiryTime - now) / 1000;
            
            if (timeLeft <= 0) {
                clearInterval(otpData.timerInterval);
                $("#timer_bar").css('width', '0%');
                $("#timer_text").text('0:00');
                $("#otp_status_badge").text('Expired').css('background', 'var(--color-background-danger)').css('color', 'var(--color-text-danger)');
                showMessage('OTP has expired', 'warning');
                return;
            }
            
            const minutes = Math.floor(timeLeft / 60);
            const seconds = Math.floor(timeLeft % 60);
            const displayTime = minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
            
            $("#timer_text").text(displayTime);
            
            // Update progress bar
            const percentageLeft = (timeLeft / otpData.validity) * 100;
            $("#timer_bar").css('width', percentageLeft + '%');
            
            // Update expiry display
            const expiryHours = otpData.expiryTime.getHours().toString().padStart(2, '0');
            const expiryMinutes = otpData.expiryTime.getMinutes().toString().padStart(2, '0');
            const expirySecs = otpData.expiryTime.getSeconds().toString().padStart(2, '0');
            $("#otp_expiry_display").text(expiryHours + ':' + expiryMinutes + ':' + expirySecs);
            
            // Change color when time is running out
            if (timeLeft < 60) {
                $("#timer_bar").css('background', 'var(--color-background-danger)');
            } else if (timeLeft < 120) {
                $("#timer_bar").css('background', 'var(--color-background-warning)');
            }
        }, 1000);
        
        // Initial update
        const minutes = Math.floor(otpData.validity / 60);
        const seconds = otpData.validity % 60;
        $("#timer_text").text(minutes + ':' + (seconds < 10 ? '0' : '') + seconds);
        $("#timer_bar").css('width', '100%').css('background', 'var(--color-background-warning)');
    }

    // Copy OTP
    $("#copy_otp_btn").click(function() {
        if (otpData.code) {
            navigator.clipboard.writeText(otpData.code).then(() => {
                const originalText = $(this).text();
                $(this).text('✓ Copied!');
                setTimeout(() => {
                    $(this).text(originalText);
                }, 2000);
                showMessage('OTP copied to clipboard', 'success');
            }).catch(err => {
                showMessage('Failed to copy OTP', 'error');
            });
        }
    });

    // Clear All
    $("#clear_otp_btn").click(function() {
        $("#otp_info_container").hide();
        $("#mobile_no").val('');
        $("#message_container").hide();
        if (otpData.timerInterval) {
            clearInterval(otpData.timerInterval);
        }
        otpData = {};
    });

    // Format mobile number (hide middle digits)
    function formatMobileNumber(mobile) {
        if (!mobile || mobile.length < 10) return mobile;
        return mobile.substring(0, 3) + '****' + mobile.substring(7);
    }

    // Show message
    function showMessage(message, type) {
        const alertMessage = $("#alert_message");
        
        let bgColor, textColor, borderColor;
        if (type === 'success') {
            bgColor = 'var(--color-background-success)';
            textColor = 'var(--color-text-success)';
            borderColor = 'var(--color-border-success)';
        } else if (type === 'error') {
            bgColor = 'var(--color-background-danger)';
            textColor = 'var(--color-text-danger)';
            borderColor = 'var(--color-border-danger)';
        } else if (type === 'warning') {
            bgColor = 'var(--color-background-warning)';
            textColor = 'var(--color-text-warning)';
            borderColor = 'var(--color-border-warning)';
        }
        
        alertMessage.text(message)
            .css('background', bgColor)
            .css('color', textColor)
            .css('border-left-color', borderColor);
        
        $("#message_container").show();
        
        // Auto hide success messages
        if (type === 'success') {
            setTimeout(() => {
                $("#message_container").fadeOut();
            }, 3000);
        }
    }
}