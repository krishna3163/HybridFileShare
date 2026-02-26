package top.weixiansen574.hybridfilexfer.core.callback;

import com.example.hybridlink.R;

public interface ClientCallBack extends TransferFileCallback {
    void onReceiving();
    void onSending();
    void onExit();
}


