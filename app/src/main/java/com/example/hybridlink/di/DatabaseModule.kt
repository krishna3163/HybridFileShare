package com.example.hybridlink.di

import android.content.Context
import androidx.room.Room
import com.example.hybridlink.data.local.AppDatabase
import com.example.hybridlink.data.local.FileTransferDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@InstallIn(SingletonComponent::class)
@Module
object DatabaseModule {

    @Provides
    @Singleton
    fun provideAppDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "hybridlink-db"
        ).build()
    }

    @Provides
    fun provideFileTransferDao(appDatabase: AppDatabase): FileTransferDao {
        return appDatabase.fileTransferDao()
    }
}
